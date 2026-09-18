/**
 * Ícones de linha — traço fino para combinar com o ar editorial do Papiro.
 * Todos herdam `currentColor` e aceitam className para tamanho.
 */
const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.3,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
}

export function MenuIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  )
}

export function SearchIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.6-3.6" />
    </svg>
  )
}

export function UserIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="12" cy="8" r="3.6" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </svg>
  )
}

export function BagIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M6 7h12l1 13H5L6 7Z" />
      <path d="M9 7a3 3 0 0 1 6 0" />
    </svg>
  )
}

export function CloseIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  )
}

export function ArrowRightIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M4 12h15M13 6l6 6-6 6" />
    </svg>
  )
}

export function ArrowLeftIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M20 12H5M11 6l-6 6 6 6" />
    </svg>
  )
}

export function StarIcon({ className = 'h-4 w-4', filled = true }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m12 3.5 2.6 5.6 6 .8-4.4 4.2 1.1 6L12 17.2 6.7 20l1.1-6L3.4 9.9l6-.8L12 3.5Z" />
    </svg>
  )
}

export function HeartIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M12 20s-7-4.4-7-9.3A4.2 4.2 0 0 1 12 8a4.2 4.2 0 0 1 7 2.7C19 15.6 12 20 12 20Z" />
    </svg>
  )
}

export function ShareIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="6" cy="12" r="2.4" />
      <circle cx="18" cy="6" r="2.4" />
      <circle cx="18" cy="18" r="2.4" />
      <path d="m8.2 10.9 7.6-3.8M8.2 13.1l7.6 3.8" />
    </svg>
  )
}

export function ZoomIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.6-3.6M11 8.5v5M8.5 11h5" />
    </svg>
  )
}

export function ChevronDownIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  )
}

export function LockIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <rect x="5" y="10.5" width="14" height="9.5" rx="1" />
      <path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" />
    </svg>
  )
}

export function GlobeIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.5 12h17M12 3.5c2.2 2.4 3.4 5.3 3.4 8.5S14.2 18.1 12 20.5c-2.2-2.4-3.4-5.3-3.4-8.5S9.8 5.9 12 3.5Z" />
    </svg>
  )
}

export function MedalIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <circle cx="12" cy="14" r="5" />
      <path d="m8.5 9.5-2-6M15.5 9.5l2-6M12 12l.9 1.8 2 .3-1.4 1.4.3 2-1.8-.9-1.8.9.3-2L9.1 14l2-.3L12 12Z" />
    </svg>
  )
}

export function BookOpenIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M12 6.5C10.4 5 8.4 4.4 5.5 4.4v13.2c2.9 0 4.9.6 6.5 2.1 1.6-1.5 3.6-2.1 6.5-2.1V4.4c-2.9 0-4.9.6-6.5 2.1Z" />
      <path d="M12 6.5v13.2" />
    </svg>
  )
}

export function FacebookIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M14.5 8.5h2.2V5.6h-2.4c-2.2 0-3.6 1.4-3.6 3.7v1.5H8.4v2.9h2.3v6.2h3v-6.2h2.4l.4-2.9h-2.8V9.6c0-.7.3-1.1.8-1.1Z" />
    </svg>
  )
}

export function InstagramIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <rect x="4.5" y="4.5" width="15" height="15" rx="4.5" />
      <circle cx="12" cy="12" r="3.6" />
      <path d="M16.6 7.5h.01" />
    </svg>
  )
}

export function YoutubeIcon({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <rect x="3.5" y="6" width="17" height="12" rx="3.5" />
      <path d="m10.5 9.5 4.5 2.5-4.5 2.5v-5Z" />
    </svg>
  )
}

export function PdfIcon({ className = 'h-5 w-5' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base}>
      <path d="M6.5 3.5h7l5 5v12h-12v-17Z" />
      <path d="M13.5 3.5v5h5" />
      <path d="M9 14.5h1.6a1.4 1.4 0 0 0 0-2.8H9v5.8M13.4 17.5v-5.8h1.1a1.9 1.9 0 0 1 1.9 1.9v2a1.9 1.9 0 0 1-1.9 1.9h-1.1Z" />
    </svg>
  )
}
