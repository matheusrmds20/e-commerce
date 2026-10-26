// @ts-check
import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

/**
 * globalSetup do Playwright — roda UMA vez antes da suíte.
 *
 * Recria o banco E2E do zero (drop + migrations + seed) via script Python,
 * garantindo estoque cheio e ausência de resíduos de execuções anteriores.
 * Replica o fluxo do CI, onde o banco já nasce limpo.
 *
 * É idempotente: recriar um banco limpo não tem efeito colateral no CI.
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// Raiz do repo: frontend/Papiro/e2e -> ... -> E-commerce v1
const repoRoot = path.resolve(__dirname, '..', '..', '..')

const isWindows = process.platform === 'win32'
// Como o script é executado com cwd = repoRoot, o venv fica em raiz/venv.
const venvPy = isWindows
  ? path.join(repoRoot, 'venv', 'Scripts', 'python.exe')
  : path.join(repoRoot, 'venv', 'bin', 'python')

function resolvePython() {
  // PYTHON_BIN explícito tem prioridade.
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN
  // Vem do venv do repo (igual ao fluxo local do config).
  if (fs.existsSync(venvPy)) return venvPy
  // Fallback: python do ambiente (CI).
  return 'python'
}

export default function globalSetup() {
  const script = path.join(repoRoot, 'backend', 'scripts', 'reset_e2e_db.py')
  const py = resolvePython()

  // A URL do banco E2E vem de env (CI) ou do backend/.env (dev local); o
  // próprio script Python resolve isso (mesma lógica do e2e_server.py).
  console.log('[globalSetup] resetando banco E2E via backend/scripts/reset_e2e_db.py ...')
  execSync(`"${py}" "${script}"`, {
    cwd: repoRoot,
    stdio: 'inherit',
    env: process.env,
  })
  console.log('[globalSetup] banco E2E pronto.')
}