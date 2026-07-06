import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts'

export default function TemperatureChart({ city }) {
  if (!city) return null

  const history = city.yearlyAvgTemp.map((d) => ({
    year: d.year,
    historical: Number(d.temperature_2m_mean.toFixed(2)),
    forecast: null,
  }))

  const lastYear = history[history.length - 1].year
  const lastTemp = history[history.length - 1].historical

  const bridge = {
    year: lastYear,
    historical: lastTemp,
    forecast: lastTemp,
  }

  const forecastPoints = [
    {
      year: lastYear + 1,
      historical: null,
      forecast: Number(city.forecast.avgTempForecastYear1.toFixed(2)),
    },
    {
      year: lastYear + 2,
      historical: null,
      forecast: Number(city.forecast.avgTempForecastYear2.toFixed(2)),
    },
  ]

  const data = [...history.slice(0, -1), bridge, ...forecastPoints]

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Temperature Trend</h3>
        <p className="chart-subtitle">
          {lastYear - history[0].year + 1} years observed, 2 years forecast
          {' · '}
          <span className="warming-trend">
            {city.forecast.warmingTrendCPerDecade >= 0 ? "+" : ""}{city.forecast.warmingTrendCPerDecade.toFixed(2)}°C / decade
          </span>
        </p>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="year"
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
          />
          <YAxis
            stroke="rgba(255,255,255,0.4)"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            unit="°C"
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(19,23,34,0.95)',
              border: '1px solid rgba(52,211,153,0.3)',
              borderRadius: 10,
              color: '#E8EAF0',
              fontSize: 13,
            }}
            formatter={(value, name) => [
              value != null ? `${value}°C` : null,
              name === 'historical' ? 'Observed' : 'Forecast (ETS)',
            ]}
          />
          <ReferenceLine x={lastYear} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
          <Line
            type="monotone"
            dataKey="historical"
            stroke="#60D9EF"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#60D9EF', strokeWidth: 0 }}
            activeDot={{ r: 5 }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#34D399"
            strokeWidth={2.5}
            strokeDasharray="6 4"
            dot={{ r: 3, fill: '#34D399', strokeWidth: 0 }}
            activeDot={{ r: 5 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>

      <p className="chart-footnote">
        Dashed segment shows precomputed statsmodels ETS output, exported ahead of time -
        not a live model re-run on each view.
      </p>
    </div>
  )
}
