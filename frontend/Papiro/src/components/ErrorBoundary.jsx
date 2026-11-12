import { Component } from 'react'

/**
 * Error Boundary — evita a "tela branca" quando uma exceção de render derruba
 * a árvore de rotas (perda de venda). Mostra uma tela amigável com botão de
 * recarregar. Usado como classe porque React só tem boundary para componentes
 * de classe.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { erro: null }
  }

  static getDerivedStateFromError(erro) {
    return { erro }
  }

  componentDidCatch(erro, info) {
    // Loga no console para depuração sem derrubar o usuário.
    console.error('Erro não capturado na UI:', erro, info?.componentStack)
  }

  handleRecarregar = () => {
    this.setState({ erro: null })
    window.location.reload()
  }

  render() {
    if (this.state.erro) {
      return (
        <div
          role="alert"
          className="flex min-h-svh items-center justify-center bg-cream-tint px-4"
        >
          <div className="max-w-md text-center">
            <p className="font-body text-xs font-semibold uppercase tracking-[0.18em] text-caramel-dark">
              Algo saiu do lugar
            </p>
            <h1 className="mt-3 font-display text-3xl font-normal text-coffee">
              Ops — não conseguimos montar essa página
            </h1>
            <p className="mt-3 font-body text-sm text-coffee-soft">
              Aconteceu um erro inesperado. Tente recarregar a página; seus
              itens na sacola continuam guardados.
            </p>
            <button
              type="button"
              onClick={this.handleRecarregar}
              className="mt-6 inline-flex items-center gap-2 rounded-sm bg-forest px-6 py-3 font-body text-xs font-semibold uppercase tracking-wider text-cream-soft transition-colors hover:bg-forest-soft"
            >
              Recarregar página
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}