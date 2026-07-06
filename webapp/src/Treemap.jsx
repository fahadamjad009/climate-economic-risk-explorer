import { useMemo, useState } from 'react'
import { hierarchy, treemap as d3treemap } from 'd3-hierarchy'
import { tempToColor } from './colorScale'

export default function Treemap({ cities, selectedCity, onSelectCity }) {
  const [hovered, setHovered] = useState(null)
  const width = 900
  const height = 420

  const nodes = useMemo(() => {
    const root = hierarchy({
      name: 'root',
      children: cities.map((c) => ({
        name: c.name,
        country: c.country,
        value: Math.max(c.totalDisasterDamage, 1),
        avgTemp: c.avgTempOverall,
      })),
    }).sum((d) => d.value)

    d3treemap().size([width, height]).paddingInner(3).paddingOuter(2)(root)

    return root.leaves()
  }, [cities])

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Damage Share Treemap</h3>
        <p className="chart-subtitle">
          Tile size = share of total disaster damage. Color = average temperature.
        </p>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ overflow: 'visible' }}>
        {nodes.map((node) => {
          const w = node.x1 - node.x0
          const h = node.y1 - node.y0
          const isSelected = selectedCity?.name === node.data.name
          const isHovered = hovered === node.data.name
          const showLabel = w > 55 && h > 30

          return (
            <g
              key={node.data.name}
              onClick={() => {
                const city = cities.find((c) => c.name === node.data.name)
                if (city && onSelectCity) onSelectCity(city)
              }}
              onMouseEnter={() => setHovered(node.data.name)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}
            >
              <rect
                x={node.x0}
                y={node.y0}
                width={w}
                height={h}
                fill={tempToColor(node.data.avgTemp)}
                fillOpacity={isSelected ? 1 : isHovered ? 0.9 : 0.7}
                stroke={isSelected ? '#34D399' : 'rgba(255,255,255,0.15)'}
                strokeWidth={isSelected ? 2.5 : 1}
                rx={3}
              />
              {showLabel && (
                <text
                  x={node.x0 + 6}
                  y={node.y0 + 16}
                  fontSize="12"
                  fontWeight="600"
                  fill="#0B0D12"
                >
                  {node.data.name}
                </text>
              )}
              {showLabel && h > 45 && (
                <text
                  x={node.x0 + 6}
                  y={node.y0 + 32}
                  fontSize="11"
                  fill="rgba(11,13,18,0.75)"
                >
                  ${(node.data.value / 1e9).toFixed(1)}B
                </text>
              )}
            </g>
          )
        })}
      </svg>

      <p className="chart-footnote">
        Click a tile to select that city elsewhere on the page.
      </p>
    </div>
  )
}
