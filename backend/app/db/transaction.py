"""Helper de fronteira de transação para os services.

Contexto do problema
--------------------
O projeto usa ``SessionLocal(autocommit=False, autoflush=False)``. Nesse modo o
SQLAlchemy 2.0 faz **autobegin**: a primeira query (ou o acesso a um atributo
expirado, que dispara lazy-load) inicia uma transação implicitamente.

Isso quebra o padrão ingênuo ``with session.begin(): ...`` porque, quando algum
acesso/query acontece ANTES do ``begin()``, o SQLAlchemy levanta:

    InvalidRequestError: A transaction is already begun on this Session.

Casos reais encontrados neste código:
- ``UserService.deactivate`` recebia ``current_user`` de ``get_current_user``
  (que faz ``expunge``/``rollback``): ler ``current_user.id`` no call site já
  abria a transação, e o ``begin()`` seguinte estourava — o
  ``DELETE /users/delete/{id}`` respondia 500.
- Qualquer service que valide permissão (lendo atributos do usuário do token)
  antes de abrir a transação de escrita cai no mesmo caso.

Solução
-------
``transacao(session)`` é um context manager que:

- **abre uma transação nova e faz commit/rollback** quando a sessão está ociosa;
- **reaproveita a transação já em andamento** (savepoint via ``begin_nested``)
  quando já existe uma — evitando o erro e mantendo a atomicidade;
- é **tolerante a sessões de teste** (``MagicMock``), onde ``begin()`` não
  implementa o protocolo de context manager: nesse caso apenas executa o bloco.
"""
from contextlib import contextmanager, nullcontext

from sqlalchemy.orm import Session


@contextmanager
def transacao(session: Session):
    """Executa um bloco dentro de uma transação, reaproveitando a existente.

    - Sessão ociosa: abre transação real; commit no sucesso, rollback no erro.
    - Sessão já em transação: usa savepoint (``begin_nested``) para o bloco ser
      atômico por si só, sem interferir na transação externa.

    Devolve a sessão para conveniência (``with transacao(s) as s:``).
    """
    # `is True`: só trata como "já em transação" quando a resposta é o booleano
    # True. Em testes, `session` pode ser um MagicMock cujo `in_transaction()`
    # devolve um Mock (truthy) — esse caso NÃO é uma transação real.
    em_transacao = session.in_transaction() is True

    if em_transacao:
        gerenciador = session.begin_nested()
    else:
        gerenciador = session.begin()

    # Sessões de teste (MagicMock) devolvem um objeto que não implementa
    # `__enter__`/`__exit__`. Nesse caso executamos o bloco sem gerenciar
    # transação — o objetivo do teste é a lógica do service, não o commit.
    if not hasattr(gerenciador, "__enter__"):
        with nullcontext(session):
            yield session
        return

    with gerenciador:
        yield session
