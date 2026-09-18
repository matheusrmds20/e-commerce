/**
 * Field — a serif-labelled input with a single hairline underline.
 * Keeps the airy, editorial rhythm of the reference layout.
 */
export default function Field({ label, id, error, children }) {
  return (
    <div className="group">
      <label
        htmlFor={id}
        className="mb-2 block font-display text-[1.125rem] font-medium text-coffee transition-colors duration-300 group-focus-within:text-gold"
      >
        {label}
      </label>

      {children}

      <div className="h-px w-full bg-line" />
      {error && (
        <p className="pt-2 font-body text-xs font-medium tracking-wide text-[#a4533f]">
          {error}
        </p>
      )}
    </div>
  )
}
