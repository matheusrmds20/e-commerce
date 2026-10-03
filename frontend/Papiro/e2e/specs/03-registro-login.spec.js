import { test, expect } from '../fixtures/base'
import { tokenNoLocalStorage } from '../helpers/auth'

/**
 * 03 — Registro + login automático + restauração de sessão no reload.
 * Usa um email único por execução (nunca colide com runs anteriores).
 */
test.describe('Registro / Login', () => {
  test('registra, entra sozinho e restaura a sessão após reload', async ({
    page,
    registrarPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')

    const dados = await registrarPelaUi({
      fullName: 'E2E Teste',
      email: emailUnico('registro'),
    })

    // 1) Login automático após o cadastro: token JWT salvo.
    const token = await tokenNoLocalStorage(page)
    expect(token).toBeTruthy()
    expect(token).not.toHaveLength(0)

    // 2) Reload → sessão restaurada via GET /auth/me (token no localStorage).
    await page.reload()
    await expect(page.getByTestId('navbar-login')).toHaveAttribute(
      'aria-label',
      new RegExp(`Minha conta — ${dados.fullName}`),
      { timeout: 15_000 },
    )
    await expect(page.locator('body')).toContainText('Dom Casmurro', {
      timeout: 15_000,
    })
  })

  test('login com credenciais existentes leva para a home logada', async ({
    page,
    registrarPelaUi,
    loginPelaUi,
    emailUnico,
  }) => {
    await page.goto('/')
    const dados = await registrarPelaUi({ email: emailUnico('login') })

    // Sai da conta (menu da navbar) e volta a entrar pela tela de login.
    await page.getByTestId('navbar-login').click()
    await page.getByRole('menuitem', { name: /Sair da conta/ }).click()

    await loginPelaUi({ email: dados.email, password: dados.password })
    await expect(page.getByTestId('navbar-login')).toHaveAttribute(
      'aria-label',
      new RegExp(`Minha conta — ${dados.fullName}`),
    )
  })
})