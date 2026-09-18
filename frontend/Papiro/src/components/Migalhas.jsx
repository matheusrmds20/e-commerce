/**
 * Migalhas — trilha de navegação "Início > ... > Título".
 */
export default function Migalhas({ itens }) {
  return (
    <nav aria-label="Trilha de navegação">
      <ol className="flex flex-wrap items-center gap-2 font-body text-[0.82rem] font-medium text-coffee-faint">
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
                  className="transition-colors duration-300 hover:text-gold"
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
