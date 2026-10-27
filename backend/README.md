# Backend — API FastAPI (Papiro)

A documentação completa do projeto (arquitetura, segurança, endpoints, deploy e
ADRs) está no [`README.md`](../README.md) da raiz.

## Comandos rápidos

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```

> As migrations ficam na **raiz** do repositório (`alembic/` + `alembic.ini`);
> rode `python -m alembic upgrade head` a partir da raiz.
