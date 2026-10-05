// @ts-check
import { defineConfig, devices } from '@playwright/test'

/**
 * Intérprete Python usado para subir o backend E2E.
 * - Windows (dev local): o venv do repo fica em `venv/Scripts/python.exe`.
 * - Linux/macOS (CI ou outro clone): o venv não é versionado, então usamos o
 *   `python` do ambiente (no CI o setup-python já o coloca no PATH).
 * Sobrescrevível via PYTHON_BIN se o seu venv estiver em outro lugar.
 */
const isWindows = process.platform === 'win32'
const pythonBin =
  process.env.PYTHON_BIN || (isWindows ? '..\\venv\\Scripts\\python.exe' : 'python')

/**
 * Config E2E do frontend "Papiro".
 * Ver: E2E_PLANO.md na raiz do repo.
 * - baseURL: front local (Vite em localhost:5173).
 * - webServer (2 entradas):
 *   1) Backend: sobe um processo NOVO apontando para o DB de teste
 *      (bookcommerce-e2e) via backend/scripts/e2e_server.py.
 *   2) Vite: dev server com VITE_API_URL local — vai DIRETO ao backend
 *      (porta 8000, banco de teste), sem depender do túnel/rede externa.
 */
export default defineConfig({
  testDir: './e2e/specs',
  timeout: 30_000,
  fullyParallel: true,
  // Limita o paralelismo: o backend E2E usa o engine padrão do SQLAlchemy
  // (pool_size=5, max_overflow=10) — com 11 workers simultâneos o pool satura
  // e o acervo fica preso em "Carregando títulos…". 3 páginas simultâneas
  // cabem folgadas no pool e a suíte fica estável.
  workers: process.env.CI ? 2 : 3,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'list' : [['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      // Backend: sempre sobe um processo novo com o DB de TESTE
      // (porta 8000 — a de dev; ver E2E_PLANO.md).
      // Comando montado conforme o SO: `cd` com separador do Windows não
      // existe no Linux do CI (e vice-versa).
      command: isWindows
        ? `cd ..\\..\\backend && ${pythonBin} scripts\\e2e_server.py`
        : `cd ../../backend && ${pythonBin} scripts/e2e_server.py`,
      url: 'http://localhost:8000/',
      reuseExistingServer: false,
      timeout: 90_000,
    },
    {
      // Vite: dev server local apontando direto ao backend de teste
      // (o default de client.js é o túnel — isolar evita banco de dev e rede).
      command: 'npm run dev',
      url: 'http://localhost:5173',
      env: { VITE_API_URL: 'http://localhost:8000/api/v1' },
      reuseExistingServer: !process.env.CI,
      timeout: 90_000,
    },
  ],
})