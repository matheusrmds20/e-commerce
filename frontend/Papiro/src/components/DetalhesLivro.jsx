import { useState } from 'react'
import Estrelas from './Estrelas'
import { ChevronDownIcon } from './Icons'

/**
 * Secao — bloco retrátil com título e conteúdo.
 * Fecha/abre com animação de altura via grid-template-rows.
 */
function Secao({ id, titulo, aberta, onToggle, children }) {
  return (
    <section className="border-t border-line">
      <h2>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={aberta}
          className="flex w-full items-center justify-between gap-4 py-6 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-gold"
        >
          <span className="font-display text-[1.6rem] font-normal text-coffee">
            {titulo}
          </span>
          <ChevronDownIcon
            className={`h-5 w-5 shrink-0 text-coffee-soft transition-transform duration-500 ease-[var(--ease-cozy)] ${
              aberta ? 'rotate-180' : ''
            }`}
          />
        </button>
      </h2>

      <div
        id={id}
        className={`grid transition-[grid-template-rows] duration-500 ease-[var(--ease-cozy)] ${
          aberta ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
        }`}
      >
        <div className="overflow-hidden">
          <div className="pb-8">{children}</div>
        </div>
      </div>
    </section>
  )
}

/** Monta a ficha técnica a partir do produto da API, omitindo campos vazios. */
function montarFicha(produto) {
  return [
    produto.isbn && ['ISBN', produto.isbn],
    produto.editora && ['Editora', produto.editora],
    produto.anoPublicacao && ['Publicação', produto.anoPublicacao],
    produto.paginas && ['Páginas', produto.paginas],
    produto.idioma && ['Idioma', produto.idioma],
  ].filter(Boolean)
}

/**
 * Formulário de nova avaliação — só aparece para usuários autenticados.
 */
function FormularioAvaliacao({ enviando, onAvaliar }) {
  const [nota, setNota] = useState(5)
  const [texto, setTexto] = useState('')

  const enviar = (event) => {
    event.preventDefault()
    if (texto.trim().length < 3) return
    onAvaliar({ rating: nota, comment: texto.trim() })
    setTexto('')
  }

  return (
    <form
      onSubmit={enviar}
      className="mb-8 rounded-md border border-line bg-cream-soft p-5"
    >
      <p className="font-body text-sm font-semibold text-coffee">
        Deixe sua avaliação
      </p>

      <div className="mt-3 flex items-center gap-3">
        <span className="font-body text-[0.88rem] text-coffee-soft">Nota:</span>
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map((valor) => (
            <button
              key={valor}
              type="button"
              onClick={() => setNota(valor)}
              aria-label={`${valor} estrela${valor > 1 ? 's' : ''}`}
              aria-pressed={nota === valor}
              className={`font-display text-[1.4rem] leading-none transition-colors duration-200 ${
                valor <= nota ? 'text-gold' : 'text-coffee-faint'
              }`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      <textarea
        value={texto}
        onChange={(event) => setTexto(event.target.value)}
        rows={3}
        maxLength={500}
        placeholder="Conte o que você achou da leitura…"
        className="mt-4 w-full resize-none rounded-sm border border-line-strong bg-cream-soft px-3 py-2.5 font-body text-sm text-coffee placeholder:text-coffee-faint focus:border-forest focus:outline-none"
      />

      <button
        type="submit"
        disabled={enviando || texto.trim().length < 3}
        className="mt-3 rounded-sm bg-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 hover:bg-forest-soft disabled:cursor-not-allowed disabled:opacity-50"
      >
        {enviando ? 'Publicando…' : 'Publicar avaliação'}
      </button>
    </form>
  )
}

/**
 * DetalhesLivro — três seções retráteis: descrição, ficha e avaliações.
 *
 * Props:
 * - `descricao`: string[] parágrafos do produto.
 * - `ficha`: produto normalizado (fonte dos dados técnicos).
 * - `avaliacoes`: lista já normalizada (`avaliacaoParaView`).
 * - `autenticado`, `enviando`, `feedback`: estado do fluxo de avaliação.
 * - `onAvaliar({rating, comment})`, `onExcluirAvaliacao(reviewId)`: ações.
 */
export default function DetalhesLivro({
  descricao = [],
  ficha = {},
  avaliacoes = [],
  autenticado = false,
  enviando = false,
  feedback = null,
  onAvaliar,
  onExcluirAvaliacao,
}) {
  const [aberta, setAberta] = useState('descricao')

  const alternar = (id) => setAberta((atual) => (atual === id ? null : id))

  const fichaTecnica = montarFicha(ficha)

  return (
    <div className="grid gap-x-10 lg:grid-cols-3">
      <Secao
        titulo="Descrição do livro"
        aberta={aberta === 'descricao'}
        onToggle={() => alternar('descricao')}
      >
        <div className="flex flex-col gap-4">
          {descricao.length === 0 && (
            <p className="font-body text-[0.98rem] text-coffee-soft">
              Sem descrição cadastrada para este livro.
            </p>
          )}
          {descricao.map((paragrafo, i) => (
            <p
              key={i}
              className="font-body text-[0.98rem] font-normal leading-relaxed text-coffee-soft"
            >
              {paragrafo}
            </p>
          ))}
        </div>
      </Secao>

      <Secao
        titulo="Detalhes"
        aberta={aberta === 'detalhes'}
        onToggle={() => alternar('detalhes')}
      >
        <dl className="flex flex-col gap-3">
          {fichaTecnica.length === 0 && (
            <p className="font-body text-[0.92rem] text-coffee-soft">
              Ficha técnica indisponível.
            </p>
          )}
          {fichaTecnica.map(([rotulo, valor]) => (
            <div key={rotulo} className="flex gap-2 font-body text-[0.92rem]">
              <dt className="text-coffee-soft font-medium">{rotulo}:</dt>
              <dd className="text-coffee font-semibold">{valor}</dd>
            </div>
          ))}
        </dl>
      </Secao>

      <Secao
        id="secao-avaliacoes"
        titulo="Avaliações"
        aberta={aberta === 'avaliacoes'}
        onToggle={() => alternar('avaliacoes')}
      >
        {feedback && (
          <p
            className={`mb-5 rounded-sm px-4 py-3 font-body text-[0.88rem] ${
              feedback.tipo === 'erro'
                ? 'bg-caramel-dark/10 text-caramel-dark'
                : 'bg-forest/10 text-forest'
            }`}
          >
            {feedback.texto}
          </p>
        )}

        {autenticado ? (
          <FormularioAvaliacao enviando={enviando} onAvaliar={onAvaliar} />
        ) : (
          <p className="mb-6 font-body text-[0.88rem] text-coffee-soft">
            Entre na sua conta para avaliar este livro.
          </p>
        )}

        <ul className="flex flex-col gap-5">
          {avaliacoes.length === 0 && (
            <li className="font-body text-[0.92rem] text-coffee-soft">
              Ainda não há avaliações para este livro.
            </li>
          )}
          {avaliacoes.map((item) => (
            <li key={item.id}>
              <div className="flex items-center gap-3">
                <Estrelas nota={item.nota} />
                <span className="font-display text-[1.15rem] font-medium text-coffee">
                  {item.nome}
                </span>
                {item.proprio && onExcluirAvaliacao && (
                  <button
                    type="button"
                    onClick={() => onExcluirAvaliacao(item.id)}
                    className="ml-auto font-body text-[0.78rem] font-medium text-coffee-faint transition-colors duration-300 hover:text-caramel-dark"
                  >
                    Excluir
                  </button>
                )}
              </div>
              <p className="mt-1.5 font-body text-[0.92rem] font-normal leading-relaxed text-coffee-soft">
                {item.texto || 'Sem comentário.'}
              </p>
            </li>
          ))}
        </ul>
      </Secao>
    </div>
  )
}
