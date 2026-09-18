import { useCallback, useEffect, useState } from 'react'
import Hero from '../components/Hero'
import SlidePromocoes from '../components/SlidePromocoes'
import LivrosDestaque from '../components/LivrosDestaque'
import ProximaLeitura from '../components/ProximaLeitura'
import RecomendacaoDestaque from '../components/RecomendacaoDestaque'
import Diferenciais from '../components/Diferenciais'
import Newsletter from '../components/Newsletter'
import { carregarHome } from '../api/home'

/**
 * Home — a vitrine do Papiro, alimentada pela API.
 *
 * Fluxo:
 * 1. `carregarHome()` busca catálogo, ofertas, categorias e a recomendação
 *    da casa (com nota média das avaliações) em paralelo.
 * 2. Cada seção recebe seus dados + estado (carregando/erro/vazio).
 * 3. Falha do catálogo mostra um aviso com "tentar de novo"; falhas parciais
 *    apenas esvaziam a seção correspondente.
 *
 * Navbar e Footer ficam no App, compartilhados por todas as páginas.
 */
export default function Home({ onAbrirLivro }) {
  const [dados, setDados] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  const carregar = useCallback(async () => {
    setCarregando(true)
    setErro(null)
    try {
      setDados(await carregarHome())
    } catch (error) {
      setErro(error)
      setDados(null)
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    carregar()
  }, [carregar])

  // Erro total (catálogo indisponível): mantém Hero/Diferenciais/Newsletter
  // estáticos e sinaliza a falha no lugar das seções de dados.
  if (erro && !carregando) {
    return (
      <main>
        <Hero />
        <section className="bg-cream-soft py-20">
          <div className="mx-auto max-w-[640px] px-5 text-center sm:px-8">
            <p className="label-caps text-caramel">Catálogo indisponível</p>
            <h2 className="mt-3 font-display text-[2rem] font-normal text-forest">
              Não conseguimos carregar os livros agora
            </h2>
            <p className="mt-3 font-body text-[0.95rem] text-coffee-soft">
              {erro.message ?? 'Verifique sua conexão e tente novamente.'}
            </p>
            <button
              type="button"
              onClick={carregar}
              className="mt-7 inline-flex items-center justify-center rounded-sm bg-forest px-8 py-4 font-body text-xs font-semibold uppercase tracking-[0.2em] text-cream-soft transition-colors duration-300 hover:bg-forest-soft"
            >
              Tentar de novo
            </button>
          </div>
        </section>
        <Diferenciais />
        <Newsletter />
      </main>
    )
  }

  const { catalogo = [], ofertas = [], categorias = [], recomendacao = null } =
    dados ?? {}

  return (
    <main>
      <Hero />
      <SlidePromocoes
        ofertas={ofertas}
        carregando={carregando}
        onAbrirLivro={onAbrirLivro}
      />
      <LivrosDestaque
        livros={catalogo}
        categorias={categorias}
        carregando={carregando}
        onAbrirLivro={onAbrirLivro}
      />
      <ProximaLeitura colecoes={categorias} carregando={carregando} />
      <RecomendacaoDestaque
        recomendacao={recomendacao}
        carregando={carregando}
        onAbrirLivro={onAbrirLivro}
      />
      <Diferenciais />
      <Newsletter />
    </main>
  )
}
