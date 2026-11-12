
export default function TextLink({ href = '#', children, className = '', onClick }) {
  return (
    <a
      href={href}
      onClick={onClick}
      className={`group relative inline-block font-body text-xs tracking-wide text-coffee-soft transition-colors duration-150 hover:text-gold ${className}`}
    >
      {children}
      <span className="absolute -bottom-0.5 left-0 h-px w-0 bg-gold transition-[width] duration-150 ease-[var(--ease-cozy)] group-hover:w-full" />
    </a>
  )
}
