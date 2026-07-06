import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

function quantile(sortedArr, q) {
  const pos = (sortedArr.length - 1) * q
  const base = Math.floor(pos)
  const rest = pos - base
  if (sortedArr[base + 1] !== undefined) {
    return sortedArr[base] + rest * (sortedArr[base + 1] - sortedArr[base])
  }
  return sortedArr[base]
}

function statsFor(values) {
  const sorted = [...values].sort((a, b) => a - b)
  return {
    min: sorted[0],
    q1: quantile(sorted, 0.25),
    median: quantile(sorted, 0.5),
    q3: quantile(sorted, 0.75),
    max: sorted[sorted.length - 1],
  }
}

export default function BoxplotChart({ cities }) {
  const [hovered, setHovered] = useState(null)

  const years = [
    ...new Set(cities.flatMap((c) => c.yearlyFeatures.map((f) => f.year))),
  ].sort((a, b) => a - b)

  const byYear = years.map((year) => {
    const temps = cities
      .flatMap((c) => c.yearlyFeatures.filter((f) => f.year === year))
      .map((f) => f.avg_temp_c)
    return { year, ...statsFor(temps) }
  })

  const globalMin = Math.min(...byYear.map((y) => y.min))
  const globalMax = Math.max(...byYear.map((y) => y.max))
  const pad = (globalMax - globalMin) * 0.08

  const width = 900
  const height = 320
  const marginLeft = 50
  const marginRight = 20
  const marginTop = 20
  const marginBottom = 36
  const plotWidth = width - marginLeft - marginRight
  const plotHeight = height - marginTop - marginBottom

  const yToPx = (val) =>
    marginTop +
    plotHeight -
    ((val - (globalMin - pad)) / (globalMax + pad - (globalMin - pad))) * plotHeight

  const bandWidth = plotWidth / years.length
  const boxWidth = bandWidth * 0.45

  const yTicks = 5
  const tickValues = Array.from({ length: yTicks + 1 }, (_, i) =>
    Math.round(globalMin - pad + ((globalMax + pad - (globalMin - pad)) / yTicks) * i)
  )

  return (
    <div className="chart-card boxplot-container">
      <div className="chart-card-header">
        <h3>Temperature Distribution by Year</h3>
        <p className="chart-subtitle">
          Spread of average temperatures across all {cities.length} cities, 2016-2025
        </p>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} width="100%" style={{ overflow: 'visible' }}>
        {tickValues.map((tv) => (
          <g key={tv}>
            <line
              x1={marginLeft}
              x2={width - marginRight}
              y1={yToPx(tv)}
              y2={yToPx(tv)}
              stroke="rgba(255,255,255,0.06)"
              strokeDasharray="3 3"
            />
            <text
              x={marginLeft - 10}
              y={yToPx(tv)}
              textAnchor="end"
              dominantBaseline="middle"
              fill="rgba(255,255,255,0.4)"
              fontSize="11"
            >
              {tv}°C
            </text>
          </g>
        ))}

        {byYear.map((d, i) => {
          const cx = marginLeft + bandWidth * i + bandWidth / 2
          const isHovered = hovered === d.year
          return (
            <g
              key={d.year}
              onMouseEnter={() => setHovered(d.year)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}
            >
              <rect
                x={cx - bandWidth / 2}
                y={marginTop}
                width={bandWidth}
                height={plotHeight}
                fill="transparent"
              />
              <line
                x1={cx}
                x2={cx}
                y1={yToPx(d.max)}
                y2={yToPx(d.q3)}
                stroke="rgba(96, 217, 239, 0.6)"
                strokeWidth={1.5}
              />
              <line
                x1={cx}
                x2={cx}
                y1={yToPx(d.q1)}
                y2={yToPx(d.min)}
                stroke="rgba(96, 217, 239, 0.6)"
                strokeWidth={1.5}
              />
              <line
                x1={cx - boxWidth / 4}
                x2={cx + boxWidth / 4}
                y1={yToPx(d.max)}
                y2={yToPx(d.max)}
                stroke="rgba(96, 217, 239, 0.6)"
                strokeWidth={1.5}
              />
              <line
                x1={cx - boxWidth / 4}
                x2={cx + boxWidth / 4}
                y1={yToPx(d.min)}
                y2={yToPx(d.min)}
                stroke="rgba(96, 217, 239, 0.6)"
                strokeWidth={1.5}
              />
              <rect
                x={cx - boxWidth / 2}
                y={yToPx(d.q3)}
                width={boxWidth}
                height={yToPx(d.q1) - yToPx(d.q3)}
                fill={isHovered ? 'rgba(52, 211, 153, 0.25)' : 'rgba(96, 217, 239, 0.18)'}
                stroke={isHovered ? '#34D399' : 'rgba(96, 217, 239, 0.7)'}
                strokeWidth={1.5}
                rx={3}
              />
              <line
                x1={cx - boxWidth / 2}
                x2={cx + boxWidth / 2}
                y1={yToPx(d.median)}
                y2={yToPx(d.median)}
                stroke={isHovered ? '#34D399' : '#E8EAF0'}
                strokeWidth={2}
              />
              <text
                x={cx}
                y={height - marginBottom + 20}
                textAnchor="middle"
                fill="rgba(255,255,255,0.5)"
                fontSize="11"
              >
                {d.year}
              </text>
            </g>
          )
        })}
      </svg>

      <AnimatePresence>
        {hovered && (
          <motion.div
            className="map-tooltip boxplot-tooltip"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.15 }}
          >
            {(() => {
              const d = byYear.find((y) => y.year === hovered)
              return (
                <>
                  <strong>{d.year}</strong>
                  <div>Median: {d.median.toFixed(1)}°C</div>
                  <div>
                    IQR: {d.q1.toFixed(1)}°C - {d.q3.toFixed(1)}°C
                  </div>
                  <div>
                    Range: {d.min.toFixed(1)}°C - {d.max.toFixed(1)}°C
                  </div>
                </>
              )
            })()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
