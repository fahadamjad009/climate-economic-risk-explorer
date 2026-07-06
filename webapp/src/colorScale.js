export function tempToColor(temp, vmin = 10, vmax = 30) {
  const t = Math.max(0, Math.min(1, (temp - vmin) / (vmax - vmin)))
  const r = Math.round(60 + t * 195)
  const g = Math.round(120 + (1 - Math.abs(t - 0.5) * 2) * 90)
  const b = Math.round(240 - t * 190)
  return `rgb(${r}, ${g}, ${b})`
}
