// Floodlight rig silhouettes for the background layer: two pylons with lamp
// banks, drawn as simple geometry so they read at a glance and stay original.
export function Floodlights() {
  const bank = (x: number) => (
    <g transform={`translate(${x} 0)`}>
      <rect x="-60" y="18" width="120" height="54" fill="#141416" />
      {Array.from({ length: 12 }, (_, i) => (
        <rect key={i} x={-54 + (i % 6) * 19} y={24 + Math.floor(i / 6) * 24} width="14" height="16" fill="#F4F1EA" opacity="0.85" />
      ))}
      <rect x="-5" y="72" width="10" height="200" fill="#141416" />
      <path d="M-5 120 L-40 272 M5 120 L40 272" stroke="#141416" strokeWidth="6" />
    </g>
  );
  return (
    <svg className="bg-floodlights" viewBox="0 0 1440 240" preserveAspectRatio="xMidYMin slice" aria-hidden>
      <defs>
        <linearGradient id="beam" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#F4F1EA" stopOpacity="0.16" />
          <stop offset="1" stopColor="#F4F1EA" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M60 60 L-200 240 L520 240 Z" fill="url(#beam)" />
      <path d="M1380 60 L920 240 L1640 240 Z" fill="url(#beam)" />
      {bank(80)}
      {bank(1360)}
    </svg>
  );
}
