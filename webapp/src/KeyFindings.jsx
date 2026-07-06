function CityChip({ name, onSelectCity, cities, isSelected }) {
  return (
    <button
      className={`city-chip-inline${isSelected ? ' selected' : ''}`}
      onClick={() => {
        const city = cities.find((c) => c.name === name)
        if (city && onSelectCity) onSelectCity(city)
      }}
    >
      {name}
    </button>
  )
}

export default function KeyFindings({ keyFindings, cities, selectedCity, onSelectCity }) {
  const { priorityCities, humanitarianPriorityCities, fastestWarmingCities } = keyFindings

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>Key Findings</h3>
        <p className="chart-subtitle">
          Auto-generated from precomputed model scores and observed trends across all 30 cities.
        </p>
      </div>

      <div className="findings-section">
        <p className="findings-text">
          Based on precomputed heat-anomaly and high-damage-year risk scores, the highest
          combined-risk cities are:
        </p>
        <div className="chip-row">
          {priorityCities.map((name) => (
            <CityChip
              key={name}
              name={name}
              cities={cities}
              onSelectCity={onSelectCity}
              isSelected={selectedCity?.name === name}
            />
          ))}
        </div>
      </div>

      <div className="findings-section">
        <p className="findings-text">
          Ranked by disaster deaths and people affected, the cities with the greatest
          humanitarian exposure are:
        </p>
        <div className="chip-row">
          {humanitarianPriorityCities.map((name) => (
            <CityChip
              key={name}
              name={name}
              cities={cities}
              onSelectCity={onSelectCity}
              isSelected={selectedCity?.name === name}
            />
          ))}
        </div>
      </div>

      <div className="findings-section">
        <p className="findings-text">
          The fastest-warming cities in the dataset, by observed °C-per-decade trend, are:
        </p>
        <div className="chip-row">
          {fastestWarmingCities.map((f) => (
            <button
              key={f.city}
              className={`city-chip-inline${selectedCity?.name === f.city ? ' selected' : ''}`}
              onClick={() => {
                const city = cities.find((c) => c.name === f.city)
                if (city && onSelectCity) onSelectCity(city)
              }}
            >
              {f.city} <span className="chip-trend">+{f.trend}°C/decade</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
