import { useState } from 'react'

const FEATURES = [
  { key: 'avg_temp_c', label: 'Avg Temp' },
  { key: 'max_temp_c', label: 'Max Temp' },
  { key: 'total_precip_mm', label: 'Precip' },
  { key: 'days_over_35c', label: 'Days >35C' },
  { key: 'gdp_current_usd', label: 'GDP' },
  { key: 'population', label: 'Population' },
  { key: 'disaster_event_count', label: 'Disaster Events' },
  { key: 'disaster_deaths', label: 'Deaths' },
  { key: 'disaster_damage_usd', label: 'Damage' },
]

function pearson(x, y) {
  const n = x.length
  const meanX = x.reduce((a, b) => a + b, 0) / n
  const meanY = y.reduce((a, b) => a + b, 0) / n
  let num = 0
  let denX = 0
  let denY = 0
  for (let i = 0; i < n; i++) {
    const dx = x[i] - meanX
    const dy = y[i] - meanY
    num += dx * dy
    denX += dx * dx
    denY += dy * dy
  }
  const denom = Math.sqrt(denX * denY)
  return denom === 0 ? 0 : num / denom
}

function cellColor(r) {
  const alpha = Math.min(Math.abs(r), 1) * 0.85
  if (r >= 0) return `rgba(52, 211, 153, ${alpha})`
  return `rgba(245, 158, 11, ${alpha})`
}

export default function CorrelationHeatmap({ cities }) {
  const [hovered, setHovered] = useState(null)

  const rows = cities.flatMap((c) => c.yearlyFeatures)

  const columns = FEATURES.map((f) => rows.map((r) => r[f.key]))

  const matrix = FEATURES.map((_, i) =>
    FEATURES.map((_, j) => pearson(columns[i], columns[j]))
  )

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Feature Correlation</h3>
        <p className="chart-subtitle">
          Pearson correlation across {rows.length} city-year records
        </p>
      </div>

      <div className="heatmap-wrapper">
        <div
          className="heatmap-grid"
          style={{
            gridTemplateColumns: `140px repeat(${FEATURES.length}, 1fr)`,
          }}
        >
          <div />
          {FEATURES.map((f) => (
            <div key={f.key} className="heatmap-col-label">
              {f.label}
            </div>
          ))}

          {FEATURES.map((rowFeature, i) => (
            <>
              <div key={`label-${rowFeature.key}`} className="heatmap-row-label">
                {rowFeature.label}
              </div>
              {FEATURES.map((colFeature, j) => {
                const r = matrix[i][j]
                const isHovered =
                  hovered && hovered.i === i && hovered.j === j
                return (
                  <div
                    key={`${rowFeature.key}-${colFeature.key}`}
                    className="heatmap-cell"
                    style={{
                      background: cellColor(r),
                      outline: isHovered ? '2px solid #E8EAF0' : 'none',
                    }}
                    onMouseEnter={() => setHovered({ i, j })}
                    onMouseLeave={() => setHovered(null)}
                  >
                    {r.toFixed(2)}
                  </div>
                )
              })}
            </>
          ))}
        </div>
      </div>

      <p className="chart-footnote heatmap-status">
        {hovered
          ? `${FEATURES[hovered.i].label} vs ${FEATURES[hovered.j].label}: r = ${matrix[hovered.i][hovered.j].toFixed(3)}`
          : 'Hover a cell to see the exact correlation coefficient.'}
      </p>
    </div>
  )
}
