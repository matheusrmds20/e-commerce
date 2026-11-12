
export default function Migalhas({ itens }) {
  return (
    <nav aria-label="Trilha de navegação">
      <ol className="flex flex-wrap items-center gap-2 font-body text-xs font-medium text-coffee-faint">
        {itens.map((item, i) => {
          const ultimo = i === itens.length - 1
          return (
            <li key={item.rotulo} className="flex items-center gap-2">
              {ultimo ? (
                <span aria-current="page" className="font-semibold text-coffee">
                  {item.rotulo}
                </span>
              ) : (
                <a
                  href="#"
                  className="transition-colors duration-150 hover:text-gold"
                >
                  {item.rotulo}
                </a>
              )}
              {!ultimo && <span aria-hidden="true">&gt;</span>}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
