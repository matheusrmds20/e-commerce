/**
 * Feather quill — the Papiro mark.
 * Hand-drawn line-art, matching the cozy stationery feel.
 */
export default function Quill({ className = '', width = 120 }) {
  return (
    <svg
      viewBox="0 0 120 150"
      width={width}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.1"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* central shaft */}
      <path d="M84 6C58 34 38 66 30 100c-3 12-4 22-3 32" />
      {/* vane, left side */}
      <path d="M84 6c2 18-4 38-16 56-9 14-24 28-38 38" />
      {/* vane, right side */}
      <path d="M84 6c-14 4-30 16-42 32" />
      {/* barb lines */}
      <path d="M76 18c-6 10-14 18-22 24M68 34c-5 9-12 16-19 22M59 52c-5 8-11 14-17 20M50 70c-4 7-9 12-14 17M83 10c-8 12-19 22-30 30M79 26c-7 11-17 20-27 27" />
      {/* ink curl */}
      <path d="M27 132c8 6 22 8 36 5 12-2 22-8 26-14 3-5 1-9-3-8-4 1-5 5-3 8 3 5 12 6 21 2" />
    </svg>
  )
}
