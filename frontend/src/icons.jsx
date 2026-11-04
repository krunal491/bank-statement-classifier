// A small hand-rolled icon set (stroke-based, 20x20, currentColor) instead of pulling in an
// icon library for a dozen glyphs - keeps the bundle lean and every icon visually consistent.
const base = {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

function Svg({ children, ...props }) {
  return (
    <svg {...base} {...props}>
      {children}
    </svg>
  )
}

export function Logomark(props) {
  // An ascending-bars mark - stands in for the product's own identity instead of a bank emoji.
  return (
    <svg width={props.size || 22} height={props.size || 22} viewBox="0 0 24 24" fill="none" {...props}>
      <rect x="3" y="13" width="4.5" height="8" rx="1.2" fill="currentColor" opacity="0.55" />
      <rect x="9.75" y="8" width="4.5" height="13" rx="1.2" fill="currentColor" opacity="0.8" />
      <rect x="16.5" y="3" width="4.5" height="18" rx="1.2" fill="currentColor" />
    </svg>
  )
}

export const Upload = (p) => (
  <Svg {...p}>
    <path d="M12 16V4" />
    <path d="M6.5 9.5 12 4l5.5 5.5" />
    <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
  </Svg>
)

export const Lock = (p) => (
  <Svg {...p}>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
    <path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5" />
  </Svg>
)

export const Eye = (p) => (
  <Svg {...p}>
    <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
    <circle cx="12" cy="12" r="3" />
  </Svg>
)

export const EyeOff = (p) => (
  <Svg {...p}>
    <path d="M3 3l18 18" />
    <path d="M10.6 5.6A10.6 10.6 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-3.3 4.1M6.5 7.3A15.6 15.6 0 0 0 2.5 12S6 18.5 12 18.5a9.8 9.8 0 0 0 4.2-.95" />
    <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
  </Svg>
)

export const Zap = (p) => (
  <Svg {...p}>
    <path d="M12.5 3 5 13.5h5.5L11 21l7.5-10.5H13l-0.5-7.5Z" strokeLinejoin="round" />
  </Svg>
)

export const FileText = (p) => (
  <Svg {...p}>
    <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7 3.5Z" />
    <path d="M14 3.5V8h4.5" />
    <path d="M9 12.5h6M9 15.5h6M9 9.5h2" />
  </Svg>
)

export const Landmark = (p) => (
  <Svg {...p}>
    <path d="M3 10.5 12 4l9 6.5" />
    <path d="M4.5 10.5v8.5M9 10.5v8.5M15 10.5v8.5M19.5 10.5v8.5" />
    <path d="M3 20.5h18" />
  </Svg>
)

export const PieChartIcon = (p) => (
  <Svg {...p}>
    <path d="M12 3a9 9 0 1 0 9 9h-9V3Z" />
    <path d="M15 3.5A9 9 0 0 1 20.5 9H15V3.5Z" />
  </Svg>
)

export const BarChartIcon = (p) => (
  <Svg {...p}>
    <path d="M4 20.5V10M12 20.5V4M20 20.5v-7" />
  </Svg>
)

export const Repeat = (p) => (
  <Svg {...p}>
    <path d="M4 7.5h12.5a3.5 3.5 0 0 1 3.5 3.5v1" />
    <path d="M7.5 4 4 7.5 7.5 11" />
    <path d="M20 16.5H7.5A3.5 3.5 0 0 1 4 13v-1" />
    <path d="M16.5 20 20 16.5 16.5 13" />
  </Svg>
)

export const CheckCircle = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M8.5 12.3l2.3 2.3 4.7-5" />
  </Svg>
)

export const AlertTriangle = (p) => (
  <Svg {...p}>
    <path d="M12 4 21.5 20H2.5L12 4Z" strokeLinejoin="round" />
    <path d="M12 10.5v4" />
    <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
  </Svg>
)

export const Download = (p) => (
  <Svg {...p}>
    <path d="M12 3.5v12" />
    <path d="M7 11l5 5 5-5" />
    <path d="M4.5 18v1.5A1.5 1.5 0 0 0 6 21h12a1.5 1.5 0 0 0 1.5-1.5V18" />
  </Svg>
)

export const Save = (p) => (
  <Svg {...p}>
    <path d="M5 4.5h11l3 3V18A1.5 1.5 0 0 1 17.5 19.5h-11A1.5 1.5 0 0 1 5 18V4.5Z" />
    <path d="M8 4.5V9h7V4.5" />
    <path d="M8 14h8" />
  </Svg>
)

export const Search = (p) => (
  <Svg {...p}>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="m20 20-4.4-4.4" />
  </Svg>
)

export const ChevronDown = (p) => (
  <Svg {...p}>
    <path d="m6 9 6 6 6-6" />
  </Svg>
)

export const X = (p) => (
  <Svg {...p}>
    <path d="m6 6 12 12M18 6 6 18" />
  </Svg>
)

export const Sun = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4.5" />
    <path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
  </Svg>
)

export const Moon = (p) => (
  <Svg {...p}>
    <path d="M20 14.2A8.5 8.5 0 1 1 9.8 4a7 7 0 0 0 10.2 10.2Z" />
  </Svg>
)

export const TrendingUp = (p) => (
  <Svg {...p}>
    <path d="M3 17 9.5 10.5 14 15 21 7" />
    <path d="M15 7h6v6" />
  </Svg>
)

export const ArrowUpRight = (p) => (
  <Svg {...p}>
    <path d="M7 17 17 7" />
    <path d="M9 7h8v8" />
  </Svg>
)

export const ArrowDownRight = (p) => (
  <Svg {...p}>
    <path d="M7 7 17 17" />
    <path d="M17 9V17H9" />
  </Svg>
)

export const Inbox = (p) => (
  <Svg {...p}>
    <path d="M3.5 12.5h5l1.5 2.5h4l1.5-2.5h5" />
    <path d="M5.5 5.5h13l2 7v6A1.5 1.5 0 0 1 19 20H5a1.5 1.5 0 0 1-1.5-1.5v-6l2-7Z" />
  </Svg>
)

export const SlidersIcon = (p) => (
  <Svg {...p}>
    <path d="M5 6.5h7M16 6.5h3M5 12h10M18 12h1M5 17.5h3M11 17.5h8" />
    <circle cx="14" cy="6.5" r="2" />
    <circle cx="13" cy="12" r="2" />
    <circle cx="8" cy="17.5" r="2" />
  </Svg>
)
