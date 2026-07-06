import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from 'recharts'

export default function QuadrantScatter({
  cities,
  title,
  subtitle,
  xLabel,
  yLabel,
  xAccessor,
  yAccessor,
  xDivider,
  yDivider,
  xTooltipFormat,
  yTooltipFormat,
  yTickFormat = (v) => v,
  quadrantLabels,
  selectedCity,
  onSelectCity,
}) {
  const data = cities.map((c) => ({
    name: c.name,
    country: c.country,
    x: xAccessor(c),
    y: yAccessor(c),
  }))

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>{title}</h3>
        <p className="chart-subtitle">{subtitle}</p>
      </div>

      <div className="quadrant-wrapper">
        {quadrantLabels && (
          <>
            <span className="quadrant-label quadrant-top-left">
              {quadrantLabels.topLeft}
            </span>
            <span className="quadrant-label quadrant-top-right">
              {quadrantLabels.topRight}
            </span>
            <span className="quadrant-label quadrant-bottom-left">
              {quadrantLabels.bottomLeft}
            </span>
            <span className="quadrant-label quadrant-bottom-right">
              {quadrantLabels.bottomRight}
            </span>
          </>
        )}

        <ResponsiveContainer width="100%" height={340}>
          <ScatterChart margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              type="number"
              dataKey="x"
              name={xLabel}
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
              label={{
                value: xLabel,
                position: 'insideBottom',
                offset: -10,
                fill: 'rgba(255,255,255,0.5)',
                fontSize: 12,
              }}
            />
            <YAxis
              tickFormatter={yTickFormat}
              type="number"
              dataKey="y"
              name={yLabel}
              stroke="rgba(255,255,255,0.4)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              label={{
                value: yLabel,
                angle: -90,
                position: 'insideLeft',
                fill: 'rgba(255,255,255,0.5)',
                fontSize: 12,
              }}
            />
            <ReferenceLine x={xDivider} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
            <ReferenceLine y={yDivider} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{
                background: 'rgba(19,23,34,0.95)',
                border: '1px solid rgba(52,211,153,0.3)',
                borderRadius: 10,
                color: '#E8EAF0',
                fontSize: 13,
              }}
              itemStyle={{ color: '#E8EAF0' }}
              formatter={(value, name) => {
                if (name === xLabel) return [xTooltipFormat(value), xLabel]
                if (name === yLabel) return [yTooltipFormat(value), yLabel]
                return [value, name]
              }}
              labelFormatter={() => ''}
            />
            <Scatter
              data={data}
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
                      : 'rgba(96, 217, 239, 0.65)'
                  }
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
