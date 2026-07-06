import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts'

export default function DamageBarChart({ cities, selectedCity, onSelectCity }) {
  const data = [...cities]
    .sort((a, b) => b.totalDisasterDamage - a.totalDisasterDamage)
    .map((c) => ({
      name: c.name,
      country: c.country,
      damageB: Number((c.totalDisasterDamage / 1e9).toFixed(2)),
    }))

  const rowHeight = 26
  const chartHeight = data.length * rowHeight + 40

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Disaster Damage by City</h3>
        <p className="chart-subtitle">
          Total recorded damage 2016-2025, ranked highest to lowest
        </p>
      </div>

      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 30, left: 10, bottom: 0 }}
          barCategoryGap={6}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
          <XAxis
            type="number"
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
            unit="B"
          />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(19,23,34,0.95)',
              border: '1px solid rgba(52,211,153,0.3)',
              borderRadius: 10,
              color: '#E8EAF0',
              fontSize: 13,
            }}
            itemStyle={{ color: '#E8EAF0' }}
            formatter={(value, _name, props) => [
              `$${value}B`,
              props.payload.country,
            ]}
          />
          <Bar
            dataKey="damageB"
            radius={[0, 4, 4, 0]}
            onClick={(entry) => {
              const city = cities.find((c) => c.name === entry.name)
              if (city && onSelectCity) onSelectCity(city)
            }}
            style={{ cursor: 'pointer' }}
          >
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={
                  selectedCity?.name === entry.name
                    ? '#34D399'
                    : 'rgba(96, 217, 239, 0.55)'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
