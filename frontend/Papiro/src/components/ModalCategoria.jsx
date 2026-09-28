import { useState } from 'react'
import { CloseIcon } from './Icons'

/**
 * Modal de criação/edição de categorias (Painel Admin).
 *
 * Contrato com o backend (`CategoryCreate` / `CategoryUpdate`):
 *   { name, slug, description?, image_url?, is_active, parent_id? }
 *
 * Em criação, se o slug ficar vazio ele é gerado a partir do nome (mesma
 * estratégia de slug do cadastro de livros no Admin). O modal é "burro":
 * recebe `categoriaParaEditar` (null = criação), devolve tudo via
 * `onSalvar(payload, categoriaId)` e deixa o Admin atualizar a lista.
 */

/** Gera um slug simples a partir de um texto (minúsculas, hífens). */
function gerarSlug(texto) {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

const FORM_VAZIO = {
  name: '',
  slug: '',
  description: '',
  image_url: '',
  is_active: true,
}

function formInicial(categoria) {
  if (!categoria) return FORM_VAZIO
  return {
    name: categoria.name ?? '',
    slug: categoria.slug ?? '',
    description: categoria.description ?? '',
    image_url: categoria.image_url ?? '',
    is_active: categoria.is_active !== false,
  }
}

export default function ModalCategoria({
  onClose,
  onSalvar,
  categoriaParaEditar = null,
}) {
  const criando = !categoriaParaEditar
  const [form, setForm] = useState(() => formInicial(categoriaParaEditar))
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState(null)
  const [salvando, setSalvando] = useState(false)

  const setCampo = (campo, valor) =>
    setForm((atual) => ({ ...atual, [campo]: valor }))

  /** Ao sair do nome em criação, sugere o slug se o campo ainda estiver vazio. */
  const sugerirSlug = () => {
    if (criando && !form.slug.trim() && form.name.trim()) {
      setCampo('slug', gerarSlug(form.name))
    }
  }

  const validar = () => {
    const novos = {}
    if (form.name.trim().length < 3) {
      novos.name = 'O nome precisa ter ao menos 3 caracteres.'
    }
    const slug = form.slug.trim()
    if (slug.length < 3) {
      novos.slug = 'O slug precisa ter ao menos 3 caracteres.'
    } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
      novos.slug = 'Use apenas letras minúsculas, números e hífens.'
    }
    setErros(novos)
    return Object.keys(novos).length === 0
  }

  const enviar = async (event) => {
    event.preventDefault()
    setErroGeral(null)
    if (!validar()) return

    const payload = {
      name: form.name.trim(),
      slug: form.slug.trim(),
      description: form.description.trim() || null,
      image_url: form.image_url.trim() || null,
      is_active: form.is_active,
    }

    setSalvando(true)
    try {
      await onSalvar(
        payload,
        criando ? null : categoriaParaEditar.id,
      )
    } catch (error) {
      setErroGeral(error?.message ?? 'Não foi possível salvar a categoria.')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-forest/50 backdrop-blur-xs">
      <div className="w-full max-w-lg bg-cream-soft border border-line rounded-sm shadow-2xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center pb-4 border-b border-line">
          <div>
            <span className="label-caps text-gold">Curadoria</span>
            <h3 className="font-display text-2xl font-bold text-coffee mt-1">
              {criando ? 'Nova Categoria' : 'Editar Categoria'}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-coffee-faint hover:text-coffee transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        <form onSubmit={enviar} className="mt-6 space-y-4 font-body">
          {erroGeral && (
            <p className="rounded-sm bg-caramel-dark/10 px-4 py-2.5 text-[0.88rem] text-caramel-dark">
              {erroGeral}
            </p>
          )}

          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              Nome *
            </label>
            <input
              type="text"
              required
              placeholder="ex: Ficção Científica"
              value={form.name}
              onChange={(e) => setCampo('name', e.target.value)}
              onBlur={sugerirSlug}
              className="w-full campo py-2"
            />
            {erros.name && (
              <p className="mt-1 text-xs text-caramel-dark">{erros.name}</p>
            )}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              Slug *
            </label>
            <input
              type="text"
              required
              placeholder="ex: ficcao-cientifica"
              value={form.slug}
              onChange={(e) => setCampo('slug', e.target.value)}
              className="w-full campo py-2 font-mono text-xs"
            />
            {erros.slug ? (
              <p className="mt-1 text-xs text-caramel-dark">{erros.slug}</p>
            ) : (
              <p className="mt-1 text-[0.7rem] text-coffee-faint">
                Identificador na URL. Precisa ser único.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              Descrição
            </label>
            <textarea
              rows="2"
              placeholder="Breve descrição editorial da categoria..."
              value={form.description}
              onChange={(e) => setCampo('description', e.target.value)}
              maxLength={500}
              className="w-full campo py-2 text-xs"
            />
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider font-semibold text-coffee-soft mb-1">
              URL da Imagem
            </label>
            <input
              type="url"
              placeholder="https://…"
              value={form.image_url}
              onChange={(e) => setCampo('image_url', e.target.value)}
              className="w-full campo py-2 text-xs"
            />
          </div>

          <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-coffee-soft">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setCampo('is_active', e.target.checked)}
              className="h-4 w-4 accent-[#2f4f3e]"
            />
            Categoria ativa
          </label>

          <div className="flex justify-end gap-3 pt-2 border-t border-line">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 border border-line-strong text-coffee-soft text-xs uppercase tracking-wider font-semibold rounded-sm hover:text-coffee transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando}
              className="px-5 py-2.5 bg-forest text-cream text-xs uppercase tracking-wider font-semibold rounded-sm hover:bg-forest-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {salvando ? 'Salvando…' : criando ? 'Criar Categoria' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
