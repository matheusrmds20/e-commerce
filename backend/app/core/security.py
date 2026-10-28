from datetime import UTC, datetime, timedelta
from math import log2
from uuid import uuid4

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


password_hash = PasswordHash.recommended()


ENTROPIA_MINIMA_SECRET_KEY_BITS = 128

_MAX_PADRAO_REPETIDO = 64

_PROPORCAO_PADRAO_REPETIDO = 0.9



REFRESH_COOKIE_NAME = "papiro_refresh"


def hash_password(password):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)


def entropia_estimada_bits(valor: str) -> float:
    """Estima a entropia de um segredo, em bits.

    O método é o clássico "tamanho x log2(tamanho do alfabeto)": conta quantas
    classes de caracteres aparecem e assume que cada posição foi sorteada
    uniformemente daquele alfabeto.

    Limitação importante: esta métrica mede COMPRIMENTO x VARIEDADE, não
    aleatoriedade real. `"a" * 64` usa 1 classe e cai para ~0 bits (correto),
    mas `"abcabcabc..."` usa 3 classes e pontuaria alto apesar de ser periódico.
    Por isso a verificação de produção combina esta estimativa com
    `tem_padrao_repetido()`.

    Como é deliberadamente PESSIMISTA (assume alfabeto completo mesmo que a
    string use poucos símbolos distintos), ela serve como piso, não como
    garantia.
    """
    if not valor:
        return 0.0

    alfabeto = 0
    if any(c.islower() for c in valor):
        alfabeto += 26
    if any(c.isupper() for c in valor):
        alfabeto += 26
    if any(c.isdigit() for c in valor):
        alfabeto += 10
    if any(not c.isalnum() for c in valor):
        alfabeto += 33  # pontuação + símbolos ASCII imprimíveis

    if alfabeto <= 1:
        return 0.0

    return len(valor) * log2(alfabeto)


def tem_padrao_repetido(valor: str) -> bool:
    """Detecta segredos previsíveis por repetição periódica.

    Cobre o buraco da entropia por classe de caracteres: `"passwordpassword..."`
    e `"abcabcabc..."` têm variedade de caracteres, mas zero imprevisibilidade.

    Duas verificações, porque a repetição pode não ser exata no fim:

    1. **Repetição exata** de um prefixo (cobre `"abcabc"`).
    2. **Compressibilidade**: um período curto que se repete ao longo de quase
       toda a string (cobre `"teste"*6 + "12"`, que é o caso realista de quem
       digita uma palavra e completa para atingir o tamanho mínimo).

    O critério 2 usa a taxa de acerto do período sobre a string inteira: se
    um período curto explica >= 90% das posições, a chave é previsível na
    prática, mesmo com alguns caracteres de enchimento no fim.
    """
    if not valor:
        return True

    n = len(valor)

    for tamanho in range(1, min(n // 2, _MAX_PADRAO_REPETIDO) + 1):
        if n % tamanho == 0 and valor[:tamanho] * (n // tamanho) == valor:
            return True

    for tamanho in range(1, min(n // 2, _MAX_PADRAO_REPETIDO) + 1):
        periodo = valor[:tamanho]
        acertos = sum(1 for i, c in enumerate(valor) if c == periodo[i % tamanho])
        if acertos / n >= _PROPORCAO_PADRAO_REPETIDO:
            return True

    return False


def motivo_secret_key_insegura(valor: str) -> str | None:
    """Retorna o motivo da SECRET_KEY ser inaceitável, ou None se estiver ok.

    Concentra a política num lugar só, para que `app/main.py` (startup) e
    `scripts/seed.py` apliquem exatamente o mesmo critério.

    Cobre: vazio, placeholder, curto demais, repetitivo e baixa variedade.

    LIMITAÇÃO CONHECIDA: não detecta frases de dicionário levemente disfarçadas
    (ex.: 'MinhaSenhaSuperSecretaDeProducao204'), que passam com ~200 bits
    estimados. Detectar isso exigiria uma wordlist (estilo zxcvbn), fora do escopo
    desta checagem heurística. A defesa real continua sendo a recomendação de
    gerar a chave com `secrets.token_urlsafe(32)`.
    """
    if not valor or not valor.strip():
        return "SECRET_KEY vazia."

    if valor.startswith("change-me"):
        return (
            "SECRET_KEY ainda é o placeholder 'change-me...' do .env.example. "
            "Gere uma chave real."
        )

    if len(valor) < 32:
        return f"SECRET_KEY tem apenas {len(valor)} caracteres (mínimo 32)."

    if tem_padrao_repetido(valor):
        return (
            "SECRET_KEY é a repetição de um padrão curto (ex.: 'abcabc...'), "
            "o que a torna trivialmente adivinhável apesar do tamanho."
        )

    bits = entropia_estimada_bits(valor)
    if bits < ENTROPIA_MINIMA_SECRET_KEY_BITS:
        return (
            f"SECRET_KEY tem entropia estimada de {bits:.0f} bits "
            f"(mínimo {ENTROPIA_MINIMA_SECRET_KEY_BITS}). "
            "Varie as classes de caracteres e/ou aumente o comprimento."
        )

    return None


def _create_jwt(
    data: dict,
    expires_delta: timedelta,
    token_type: str,
    jti: str | None = None,
) -> str:
    """Gera um JWT com claims de segurança (sub, jti, type, iat, exp)."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    to_encode.update(
        {
            "jti": jti or str(uuid4()),
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta = None):
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt(data, expires_delta, token_type="access")


def create_refresh_token(
    data: dict,
    expires_delta: timedelta = None,
    jti: str | None = None,
):
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_jwt(data, expires_delta, token_type="refresh", jti=jti)


def decode_token(token: str) -> dict:

    options = {"verify_signature": True, "verify_exp": True}
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options=options,
    )
