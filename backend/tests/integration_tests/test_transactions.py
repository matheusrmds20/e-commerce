"""Testes de integração de TRANSAÇÃO com SQLite real (sem mocks de sessão).

Motivação: os testes unitários usam ``MagicMock`` para a sessão, então NUNCA
pegam erros de fronteira de transação do SQLAlchemy — foi assim que o
``InvalidRequestError: A transaction is already begun`` passou despercebido e
quebrou o ``DELETE /users/delete/{id}`` (o ``UserService`` abria
``with session.begin()`` e chamava um repositório que abria um segundo
``begin()``).

Aqui usamos uma sessão REAL (SQLite em memória) e repositórios reais, de modo
que qualquer ``begin()`` aninhado ou ``commit()`` dentro de ``begin()``
estoura. Não precisamos de Postgres: o defeito é de protocolo de transação, não
de lock de linha. (Locks ``FOR UPDATE`` reais continuam cobertos pelo
``test_cart_concurrency.py``, que exige Postgres.)

Roda na suíte padrão (não marcado como ``integration``) porque SQLite
em memória está sempre disponível e o teste é rápido.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.exceptions import UserNotFoundException
from app.db.base import Base
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService


@pytest.fixture
def real_session():
    """Sessão SQLAlchemy real sobre SQLite em memória.

    ``StaticPool`` + ``check_same_thread=False`` mantêm a MESMA conexão viva
    entre o teste e a sessão (o ``:memory:`` some quando a conexão fecha).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _criar_usuario(session, **kwargs):
    fields = dict(
        email="user@example.com",
        full_name="John Doe",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    fields.update(kwargs)
    user = User(**fields)
    session.add(user)
    session.commit()
    return user


class TestDeactivateNaoQuebraTransacao:
    """Regressão: `UserService.deactivate` + `UserRepository.deactivate`.

    Antes o service abria uma transação e o repositório abria OUTRA, o que
    levanta ``InvalidRequestError``. Com o repositório sem ``begin()`` próprio,
    a operação completa normalmente.
    """

    def test_deactivate_persiste_com_sessao_real(self, real_session):
        user = _criar_usuario(real_session, email="a@example.com")
        service = UserService(real_session)

        # Ator é o próprio usuário (regra dono-ou-admin).
        resultado = service.deactivate(user.id, user)

        assert resultado.is_active is False

        # Confirma no banco (não apenas no objeto em memória).
        real_session.expire_all()
        recarregado = real_session.get(User, user.id)
        assert recarregado.is_active is False

    def test_deactivate_usuario_inexistente_levanta_404(self, real_session):
        service = UserService(real_session)
        ator = _criar_usuario(real_session, email="ator@example.com")

        # Admin pode alvejar qualquer id, inclusive inexistente.
        ator.role = UserRole.ADMIN
        real_session.commit()

        with pytest.raises(UserNotFoundException):
            service.deactivate(999, ator)


class TestRepositorioNaoGerenciaTransacao:
    """O repositório não deve abrir ``begin()`` — quem orquestra é o service."""

    def test_deactivate_do_repo_funciona_dentro_de_begin_do_service(
        self, real_session
    ):
        user = _criar_usuario(real_session, email="b@example.com")
        repo = UserRepository(real_session)

        # O service já está numa transação; o repo NÃO pode abrir outra.
        with real_session.begin():
            atualizado = repo.deactivate(user.id)

        assert atualizado is not None
        assert atualizado.is_active is False


class TestAutobeginDoUsuarioDoToken:
    """Regressão do segundo ``begin()`` aninhado.

    O ``current_user`` vem de ``get_current_user`` (que faz ``expunge``/
    ``rollback``). Acessar seus atributos (``.id``, ``.role``) dispara um
    lazy-load que inicia uma transação por autobegin. Se o service então fizer
    ``with session.begin()``, o SQLAlchemy levanta InvalidRequestError.
    ``transacao()`` trata esse caso.
    """

    def test_deactivate_apos_acessar_atributo_do_token(self, real_session):
        user = _criar_usuario(real_session, email="c@example.com")
        service = UserService(real_session)

        # Simula o que `get_current_user` + a rota fazem: o atributo é lido e
        # dispara o autobegin ANTES de o service abrir a transação.
        _ = user.id
        assert real_session.in_transaction() is True

        resultado = service.deactivate(user.id, user)

        assert resultado.is_active is False

    def test_change_password_apos_acessar_atributo_do_token(self, real_session):
        from app.core.security import hash_password

        user = _criar_usuario(
            real_session,
            email="d@example.com",
            password_hash=hash_password("senha123"),
        )
        service = UserService(real_session)

        _ = user.role  # dispara autobegin

        service.change_password(
            user.id,
            current_password="senha123",
            new_password="novaSenha456",
            current_user=user,
        )

        real_session.expire_all()
        recarregado = real_session.get(User, user.id)
        from app.core.security import verify_password

        assert verify_password("novaSenha456", recarregado.password_hash)
