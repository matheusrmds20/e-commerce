from contextlib import contextmanager, nullcontext

from sqlalchemy.orm import Session


@contextmanager
def transacao(session: Session):

    em_transacao = session.in_transaction() is True

    if em_transacao:
        gerenciador = session.begin_nested()
    else:
        gerenciador = session.begin()


    if not hasattr(gerenciador, "__enter__"):
        with nullcontext(session):
            yield session
        return

    with gerenciador:
        yield session
