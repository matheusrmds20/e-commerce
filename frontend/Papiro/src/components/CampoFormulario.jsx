
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
          className={`w-full rounded-sm border bg-cream-soft px-4 py-3.5 font-body text-[0.95rem] font-normal text-coffee placeholder:text-coffee-faint transition-colors duration-300 focus:outline-none ${
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
          className="mt-1.5 font-body text-[0.8rem] font-medium text-caramel-dark"
        >
          {erro}
        </p>
      )}
    </div>
  )
}
