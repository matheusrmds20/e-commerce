import { useState } from 'react'
import { CloseIcon } from './Icons'

const FORM_VAZIO = {
  full_name: '',
  email: '',
  password: '',
  role: 'customer',
  is_active: true,
}

function formInicial(usuario) {
  if (!usuario) return FORM_VAZIO
  return {
    full_name: usuario.full_name ?? '',
    email: usuario.email ?? '',
    password: '',
    role: usuario.role ?? 'customer',
    is_active: usuario.is_active !== false,
  }
}

/**
 * ModalUsuario — Criação e Edição de Usuários no Painel Administrativo.
 */
export default function ModalUsuario({
  onClose,
  onSalvar,
  usuarioParaEditar = null,
}) {
  const criando = !usuarioParaEditar
  const [form, setForm] = useState(() => formInicial(usuarioParaEditar))
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [salvando, setSalvando] = useState(false)

  const setCampo = (campo, valor) =>
    setForm((atual) => ({ ...atual, [campo]: valor }))

  const validar = () => {
    const novos = {}
    if (!form.full_name.trim() || form.full_name.trim().length < 3) {
      novos.full_name = 'O nome completo precisa ter ao menos 3 caracteres.'
    }
    if (!form.email.trim()) {
      novos.email = 'O e-mail é obrigatório.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      novos.email = 'Informe um e-mail válido.'
    }

    if (criando) {
      if (!form.password) {
        novos.password = 'A senha inicial é obrigatória.'
      } else {
        if (form.password.length < 8) {
          novos.password = 'A senha precisa ter no mínimo 8 caracteres.'
        } else if (!/[a-zA-Z]/.test(form.password)) {
          novos.password = 'A senha deve conter ao menos uma letra.'
        } else if (!/[0-9]/.test(form.password)) {
          novos.password = 'A senha deve conter ao menos um número.'
        }
      }
    } else if (form.password) {
      // Em edição, senha é opcional, mas se fornecida deve ser válida
      if (form.password.length < 8) {
        novos.password = 'A nova senha precisa ter no mínimo 8 caracteres.'
      } else if (!/[a-zA-Z]/.test(form.password)) {
        novos.password = 'A nova senha deve conter ao menos uma letra.'
      } else if (!/[0-9]/.test(form.password)) {
        novos.password = 'A nova senha deve conter ao menos um número.'
      }
    }

    setErros(novos)
    return Object.keys(novos).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErroGeral(null)
    if (!validar()) return

    setSalvando(true)
    try {
      const payload = {
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        role: form.role,
        is_active: form.is_active,
      }
      if (form.password) {
        payload.password = form.password
      }
      await onSalvar(payload, usuarioParaEditar?.id)
      onClose()
    } catch (err) {
      setErroGeral(err.message || 'Erro ao salvar usuário.')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-usuario-titulo"
      className="fixed inset-0 z-50 flex items-center justify-center bg-coffee/60 backdrop-blur-sm p-4 animate-fade-in"
    >
      <div className="relative w-full max-w-lg rounded-sm border border-line bg-cream-soft shadow-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div>
            <span className="label-caps text-gold">Gestão de Leitores</span>
            <h2
              id="modal-usuario-titulo"
              className="font-display text-2xl font-bold text-coffee mt-0.5"
            >
              {criando ? 'Novo Usuário' : 'Editar Usuário'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar modal"
            className="grid h-8 w-8 place-items-center text-coffee-faint hover:text-coffee transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        {erroGeral && (
          <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-xs text-red-700">
            {erroGeral}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4 font-body">
          {/* Nome Completo */}
          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              Nome Completo *
            </label>
            <input
              type="text"
              required
              value={form.full_name}
              onChange={(e) => setCampo('full_name', e.target.value)}
              placeholder="Ex: Clarice Lispector"
              className="w-full campo py-2"
            />
            {erros.full_name && (
              <p className="mt-1 text-[0.75rem] text-red-600">{erros.full_name}</p>
            )}
          </div>

          {/* E-mail */}
          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              E-mail *
            </label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setCampo('email', e.target.value)}
              placeholder="clarice@livraria.com"
              className="w-full campo py-2"
            />
            {erros.email && (
              <p className="mt-1 text-[0.75rem] text-red-600">{erros.email}</p>
            )}
          </div>

          {/* Senha */}
          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              {criando ? 'Senha Inicial *' : 'Nova Senha (deixe em branco para manter a atual)'}
            </label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setCampo('password', e.target.value)}
              placeholder={criando ? 'Mínimo 8 caracteres (letras e números)' : '••••••••'}
              className="w-full campo py-2"
            />
            {erros.password && (
              <p className="mt-1 text-[0.75rem] text-red-600">{erros.password}</p>
            )}
            <p className="mt-1 text-[0.7rem] text-coffee-faint">
              Requisitos: mínimo de 8 caracteres, contendo letras e números.
            </p>
          </div>

          {/* Perfil & Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div>
              <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                Tipo de Perfil *
              </label>
              <select
                value={form.role}
                onChange={(e) => setCampo('role', e.target.value)}
                className="w-full campo py-2 bg-cream-deep text-coffee"
              >
                <option value="customer">Leitor / Cliente (customer)</option>
                <option value="admin">Curador / Administrador (admin)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
                Status da Conta
              </label>
              <select
                value={form.is_active ? 'true' : 'false'}
                onChange={(e) => setCampo('is_active', e.target.value === 'true')}
                className="w-full campo py-2 bg-cream-deep text-coffee"
              >
                <option value="true">Ativo</option>
                <option value="false">Inativo / Bloqueado</option>
              </select>
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex justify-end gap-3 pt-5 border-t border-line mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-line-strong text-coffee-soft text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-cream-deep transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando}
              className="px-6 py-2 bg-forest hover:bg-forest-soft text-cream text-xs uppercase tracking-wider font-semibold rounded-sm transition-colors shadow-sm disabled:opacity-50"
            >
              {salvando
                ? 'Salvando...'
                : criando
                  ? 'Cadastrar Usuário'
                  : 'Salvar Alterações'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
