"""Testes da validação de entropia da SECRET_KEY.

Motivação: o guard antigo só media COMPRIMENTO (`len >= 32`), então `"a" * 64`
passava em produção. Como assinamos JWT com HS256 (simétrico: a mesma chave
assina e verifica), uma chave previsível permite forjar tokens de admin sem
senha — daí a checagem de entropia.

Estes testes existem para impedir que alguém "simplifique" a validação de volta
para uma comparação de tamanho.
"""

import secrets

import pytest

from app.core.security import (
    ENTROPIA_MINIMA_SECRET_KEY_BITS,
    entropia_estimada_bits,
    motivo_secret_key_insegura,
    tem_padrao_repetido,
)


@pytest.mark.parametrize(
    ("chave", "descricao"),
    [
        ("a" * 32, "um único caractere repetido"),
        ("a" * 64, "repetição longa (passaria no guard antigo)"),
        ("12345678901234567890123456789012", "sequência previsível"),
        ("passwordpasswordpasswordpassword", "palavra repetida"),
        ("testetestetestetestetesteteste12", "palavra repetida + enchimento"),
        ("abcabcabcabcabcabcabcabcabcabc12", "período curto + enchimento"),
    ],
)
def test_recusa_chaves_estruturalmente_fracas(chave, descricao):
    assert motivo_secret_key_insegura(chave) is not None, descricao


@pytest.mark.parametrize(
    ("chave", "trecho_esperado"),
    [
        ("change-me-to-a-random-64-char-secret-key", "placeholder"),
        ("", "vazia"),
        ("   ", "vazia"),
        ("curta", "caracteres"),
    ],
)
def test_recusa_placeholder_vazio_e_curto(chave, trecho_esperado):
    motivo = motivo_secret_key_insegura(chave)
    assert motivo is not None
    assert trecho_esperado in motivo


@pytest.mark.parametrize(
    "chave",
    [
        "Xk9#mP2$vL7@qR4&wT8*zN3!bY6^cU1%e",
        "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        secrets.token_hex(32),
    ],
)
def test_aceita_chaves_legitimas(chave):
    assert motivo_secret_key_insegura(chave) is None


def test_aceita_token_urlsafe_repetidamente():
    """`secrets.token_urlsafe(32)` é o formato recomendado: nunca pode falhar.

    Cobertura probabilística — se houver falso positivo, ele aparece aqui.
    """
    for _ in range(200):
        assert motivo_secret_key_insegura(secrets.token_urlsafe(32)) is None


def test_entropia_cresce_com_comprimento_e_variedade():
    assert entropia_estimada_bits("") == 0
    assert entropia_estimada_bits("a" * 64) < entropia_estimada_bits("aA" * 32)
    assert entropia_estimada_bits("aA1!") > entropia_estimada_bits("aaaa")


def test_entropia_minima_e_um_piso_razoavel():
    # 128 bits: padrão para segredos de longa duração.
    assert ENTROPIA_MINIMA_SECRET_KEY_BITS >= 128


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("aaaa", True),
        ("abcabc", True),
        ("abcabcabcabcabcabcabcabcabcabc12", True),
        ("testetestetestetestetesteteste12", True),
        ("Xk9#mP2$vL7@qR4&wT8*zN3!bY6^cU1%e", False),
    ],
)
def test_tem_padrao_repetido(valor, esperado):
    assert tem_padrao_repetido(valor) is esperado
