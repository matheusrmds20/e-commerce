/**
 * TextLink — quiet inline action, underline grows on hover.
 */
export default function TextLink({ href = '#', children, className = '' }) {
  return (
    <a
      href={href}
      className={`group relative inline-block font-body text-[0.8rem] tracking-wide text-coffee-soft transition-colors duration-300 hover:text-gold ${className}`}
    >
      {children}
      <span className="absolute -bottom-0.5 left-0 h-px w-0 bg-gold transition-all duration-300 ease-[var(--ease-cozy)] group-hover:w-full" />
    </a>
  )
}
