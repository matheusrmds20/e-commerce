import { useCallback, useEffect, useState } from 'react'
import Hero from '../components/Hero'
import SlidePromocoes from '../components/SlidePromocoes'
import LivrosDestaque from '../components/LivrosDestaque'
import ProximaLeitura from '../components/ProximaLeitura'
import RecomendacaoDestaque from '../components/RecomendacaoDestaque'
import Diferenciais from '../components/Diferenciais'
import Newsletter from '../components/Newsletter'
import { carregarHome } from '../api/home'


export default function Home() {
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

  const {
    catalogo = [],
    destaques = [],
    ofertas = [],
    categorias = [],
    recomendacao = null,
  } = dados ?? {}

  return (
    <main>
      <Hero />
      <SlidePromocoes ofertas={ofertas} carregando={carregando} />
      <LivrosDestaque
        livros={destaques}
        categoriaIds={catalogo}
        categorias={categorias}
        carregando={carregando}
      />
      <ProximaLeitura colecoes={categorias} carregando={carregando} />
      <RecomendacaoDestaque recomendacao={recomendacao} carregando={carregando} />
      <Diferenciais />
      <Newsletter />
    </main>
  )
}
