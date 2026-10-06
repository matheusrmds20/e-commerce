import { expect } from '@playwright/test'

/**
 * Helpers de SETUP/TEARDOWN via API (o front Vite em localhost:5173 + backend
 * E2E em localhost:8000 — ver E2E_PLANO.md).
 *
 * Cobrem cenários que a UI não consegue preparar sozinha (ex.: usuário que
 * "comprou" um livro para liberar o form de review). Sempre com o token do
 * usuário logado na página (autorização real, não injeção).
 */
export const API_URL = 'http://localhost:8000/api/v1'

/**
 * Faz login via API e retorna o access token para as chamadas de setup.
 *
 * Com a migração segura (PLANO 7.3) o access token vive SÓ em memória do
 * front (não há mais `papiro.token` no localStorage), então o setup não pode
 * lê-lo da página. Chamamos `POST /auth/login` (form-urlencoded) direto na
 * API e usamos o access token retornado nos headers das chamadas de setup.
 *
 * @returns {Promise<string>} access_token JWT (válido 15 min).
 */
export async function fazerLoginViaApi(request, { email, password }) {
  const resp = await request.post(`${API_URL}/auth/login`, {
    form: { username: email, password },
  })
  expect(
    resp.ok(),
    `login via API (setup) falhou: ${resp.status()} ${(await resp.text()).slice(0, 200)}`,
  ).toBeTruthy()
  const body = await resp.json()
  expect(body.access_token, 'login via API sem access_token').toBeTruthy()
  return body.access_token
}

/** Registra um usuário novo via API e retorna {id, email, ...}. */
export async function registrarViaApi(request, payload) {
  const resp = await request.post(`${API_URL}/auth/register`, {
    data: payload,
  })
  expect(resp.ok(), `register via API (setup) falhou: ${resp.status()}`).toBeTruthy()
  return resp.json()
}

/**
 * Cria um endereço de entrega via API (setup).
 * @returns {Promise<object>} AddressResponse ({ id, street, ... })
 */
export async function criarEnderecoViaApi(request, token, overrides = {}) {
  const resp = await request.post(`${API_URL}/addresses/create`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      street: 'Rua do Teste E2E',
      number: '123',
      neighborhood: 'Centro',
      city: 'São Paulo',
      state: 'SP',
      zip_code: '01001000',
      is_default: true,
      ...overrides,
    },
  })
  expect(
    resp.ok(),
    `criar endereço (setup) falhou: ${resp.status()} ${(await resp.text()).slice(0, 200)}`,
  ).toBeTruthy()
  return resp.json()
}

/**
 * Cria um pedido via API (setup) — torna o usuário elegível ao form de review
 * (o front considera "comprou" qualquer pedido não cancelado).
 * @param {{ address_id: number, items: {product_id: number, quantity: number}[] }} pedido
 */
export async function criarPedidoViaApi(request, token, { address_id, items }) {
  const resp = await request.post(`${API_URL}/orders/create`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { address_id, notes: 'Pedido criado no setup do E2E', items },
  })
  expect(
    resp.ok(),
    `criar pedido (setup) falhou: ${resp.status()} ${(await resp.text()).slice(0, 200)}`,
  ).toBeTruthy()
  return resp.json()
}

/** Id do primeiro produto do catálogo (para o cenário de review). */
export async function primeiroProdutoViaApi(request) {
  const resp = await request.get(`${API_URL}/products/list`)
  expect(resp.ok(), `listar produtos falhou: ${resp.status()}`).toBeTruthy()
  const lista = await resp.json()
  expect(lista.length).toBeGreaterThan(0)
  return lista[0].id
}