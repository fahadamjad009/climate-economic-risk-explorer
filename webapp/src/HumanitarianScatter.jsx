import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts'

function log1p(v) {
  return Math.log10(v + 1)
}

function formatCount(v) {
  return Math.round(v).toLocaleString()
}

export default function HumanitarianScatter({ cities, selectedCity, onSelectCity }) {
  const data = cities.flatMap((c) =>
    c.yearlyFeatures.map((f) => ({
      name: c.name,
      country: c.country,
      year: f.year,
      deaths: f.disaster_deaths,
      affected: f.disaster_affected,
      x: log1p(f.disaster_deaths),
      y: log1p(f.disaster_affected),
    }))
  )

  const maxLogX = Math.max(...data.map((d) => d.x))
  const maxLogY = Math.max(...data.map((d) => d.y))

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Humanitarian Impact</h3>
        <p className="chart-subtitle">
          Deaths vs people affected, per city-year ({data.length} records). Log scale - most
          disaster-years have zero or few casualties, and this spreads them out instead of
          crushing them into the corner.
        </p>
      </div>

      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            type="number"
            dataKey="x"
            domain={[0, maxLogX * 1.05]}
            tickFormatter={(v) => formatCount(10 ** v - 1)}
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
            label={{
              value: 'Disaster Deaths (log scale)',
              position: 'insideBottom',
              offset: -10,
              fill: 'rgba(255,255,255,0.5)',
              fontSize: 12,
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={[0, maxLogY * 1.05]}
            tickFormatter={(v) => formatCount(10 ** v - 1)}
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            label={{
              value: 'People Affected (log scale)',
              angle: -90,
              position: 'insideLeft',
              fill: 'rgba(255,255,255,0.5)',
              fontSize: 12,
            }}
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (!active || !payload || !payload.length) return null
              const d = payload[0].payload
              return (
                <div
                  style={{
                    background: 'rgba(19,23,34,0.95)',
                    border: '1px solid rgba(52,211,153,0.3)',
                    borderRadius: 10,
                    padding: '0.8rem 1.1rem',
                    fontSize: 13,
                    color: '#E8EAF0',
                  }}
                >
                  <strong>
                    {d.name}, {d.country} ({d.year})
                  </strong>
                  <div>Deaths: {formatCount(d.deaths)}</div>
                  <div>Affected: {formatCount(d.affected)}</div>
                </div>
              )
            }}
          />
          <Scatter
            data={data}
            onClick={(entry) => {
              const city = cities.find((c) => c.name === entry.name)
              if (city && onSelectCity) onSelectCity(city)
            }}
            style={{ cursor: 'pointer' }}
          >
            {data.map((entry, i) => (
              <Cell
                key={`${entry.name}-${entry.year}-${i}`}
                fill={
                  selectedCity?.name === entry.name
                    ? '#34D399'
                    : 'rgba(96, 217, 239, 0.5)'
                }
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      <p className="chart-footnote">
        Click a point to select that city elsewhere on the page.
      </p>
    </div>
  )
}
