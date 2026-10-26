import { expect } from '@playwright/test'
import { navegarPara } from './navegar'


export function emailUnico(prefixo = 'e2e') {
  return `${prefixo}_${Date.now()}_${Math.floor(Math.random() * 1000)}@exemplo.com`
}

/** Senha que passa na validação do Registro (>=8, letra + número). */
export const SENHA_E2E = 'E2eSenha123!'


export async function registrarPelaUi(page, { fullName, email, password } = {}) {
  const dados = {
    fullName: fullName ?? 'E2E Teste',
    email: email ?? emailUnico(),
    password: password ?? SENHA_E2E,
  }

  await navegarPara(page, 'registro')
  await page.getByTestId('input-full-name').fill(dados.fullName)
  await page.getByTestId('input-email').fill(dados.email)
  await page.getByTestId('input-password').fill(dados.password)
  await page.getByTestId('input-confirmacao').fill(dados.password)
  await page.getByTestId('btn-registrar').click()

  // A navbar da rota de registro é propositalmente simples e não contém o
  // botão de conta. Primeiro esperamos a confirmação e o redirecionamento
  // para a home; só então validamos a sessão na navbar completa.
  await expect(page.getByRole('status')).toContainText('Conta criada', {
    timeout: 15_000,
  })
  await page.waitForURL(/\/$/, { timeout: 15_000 })
  await expect(page.getByTestId('navbar-login')).toHaveAttribute(
    'aria-label',
    new RegExp(`Minha conta — ${dados.fullName}`),
    { timeout: 15_000 },
  )
  return dados
}

/** Faz login pela tela de login com credenciais existentes. */
export async function loginPelaUi(page, { email, password }) {
  await navegarPara(page, 'login')
  await page.getByTestId('input-email').fill(email)
  await page.getByTestId('input-password').fill(password)
  await page.getByTestId('btn-entrar').click()
  await expect(page.getByTestId('navbar-login')).toHaveAttribute(
    'aria-label',
    /Minha conta — /,
    { timeout: 15_000 },
  )
}

/** Lê o cookie httpOnly do refresh (prova de sessão ativa no browser). */
export async function refreshCookiePresente(context) {
  const cookies = await context.cookies()
  return cookies.some((c) => c.name === 'papiro_refresh')
}
