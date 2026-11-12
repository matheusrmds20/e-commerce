
export default function CampoFormulario({
  id,
  label,
  erro,
  className = '',
  children,
  ...props
}) {
  return (
    <div className={className}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>

      {children ?? (
        <input
          id={id}
          name={id}
          aria-invalid={Boolean(erro)}
          aria-describedby={erro ? `${id}-erro` : undefined}
          className={`w-full rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-sm font-normal text-coffee placeholder:text-coffee-faint transition-colors duration-150 focus:not-focus-visible:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-forest ${
            erro
              ? 'border-caramel-dark focus:border-caramel-dark'
              : 'border-line-strong focus:border-forest'
          }`}
          placeholder={label}
          {...props}
        />
      )}

      {erro && (
        <p
          id={`${id}-erro`}
          className="mt-1.5 font-body text-xs font-medium text-caramel-dark"
        >
          {erro}
        </p>
      )}
    </div>
  )
}
