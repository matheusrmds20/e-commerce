
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

    def test_deactivate_persiste_com_sessao_real(self, real_session):
        user = _criar_usuario(real_session, email="a@example.com")
        service = UserService(real_session)

        resultado = service.deactivate(user.id, user)

        assert resultado.is_active is False


        real_session.expire_all()
        recarregado = real_session.get(User, user.id)
        assert recarregado.is_active is False

    def test_deactivate_usuario_inexistente_levanta_404(self, real_session):
        service = UserService(real_session)
        ator = _criar_usuario(real_session, email="ator@example.com")


        ator.role = UserRole.ADMIN
        real_session.commit()

        with pytest.raises(UserNotFoundException):
            service.deactivate(999, ator)


class TestRepositorioNaoGerenciaTransacao:


    def test_deactivate_do_repo_funciona_dentro_de_begin_do_service(
        self, real_session
    ):
        user = _criar_usuario(real_session, email="b@example.com")
        repo = UserRepository(real_session)


        with real_session.begin():
            atualizado = repo.deactivate(user.id)

        assert atualizado is not None
        assert atualizado.is_active is False


class TestAutobeginDoUsuarioDoToken:


    def test_deactivate_apos_acessar_atributo_do_token(self, real_session):
        user = _criar_usuario(real_session, email="c@example.com")
        service = UserService(real_session)


        
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
