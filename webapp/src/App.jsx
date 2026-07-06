import { useState } from 'react'
import { motion } from 'framer-motion'
import Typewriter from './Typewriter'
import WorldMap from './WorldMap'
import TemperatureChart from './TemperatureChart'
import DamageBarChart from './DamageBarChart'
import BoxplotChart from './BoxplotChart'
import CorrelationHeatmap from './CorrelationHeatmap'
import Treemap from './Treemap'
import QuadrantScatter from './QuadrantScatter'
import HumanitarianScatter from './HumanitarianScatter'
import KeyFindings from './KeyFindings'
import data from './data/static_export.json'
import './App.css'

const TAGLINES = [
  '10 years of weather, GDP, and disaster data across 30 cities.',
  'XGBoost models scoring live heat and disaster risk.',
  'Statsmodels ETS forecasting temperature 2 years ahead.',
  'A risk matrix for prioritizing climate-adaptation investment.',
]

function KpiCard({ label, value, delay }) {
  return (
    <motion.div
      className="kpi-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -4, transition: { duration: 0.15 } }}
    >
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </motion.div>
  )
}

function CityChip({ city, isSelected, onClick }) {
  return (
    <motion.button
      className={`city-chip ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.12 }}
    >
      {city.name}
    </motion.button>
  )
}

function App() {
  const [selectedCity, setSelectedCity] = useState(
    data.cities.find((c) => c.name === 'Sydney') || data.cities[0]
  )

  const { globalStats } = data

  return (
    <div className="app">
      <motion.h1
        className="hero-title"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        Climate-Economic <span className="hero-accent">Risk Explorer</span>
      </motion.h1>
      <motion.p
        className="hero-subtitle"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <Typewriter phrases={TAGLINES} />
      </motion.p>

      <div className="chip-label">// SELECT A CITY</div>
      <div className="chip-grid">
        {data.cities.map((city) => (
          <CityChip
            key={city.name}
            city={city}
            isSelected={selectedCity.name === city.name}
            onClick={() => setSelectedCity(city)}
          />
        ))}
      </div>
      <p className="city-caption">
        {selectedCity.name}, {selectedCity.country} · {selectedCity.lat.toFixed(2)}, {selectedCity.lon.toFixed(2)}
      </p>

      <div className="kpi-row">
        <KpiCard label="Cities Tracked" value={globalStats.citiesTracked} delay={0} />
        <KpiCard label="Global Avg Temp" value={`${globalStats.globalAvgTemp.toFixed(1)}°C`} delay={0.05} />
        <KpiCard label="Total Disaster Events" value={globalStats.totalDisasterEvents.toLocaleString()} delay={0.1} />
        <KpiCard label="Total Damage (USD)" value={`$${(globalStats.totalDamageUsd / 1e9).toFixed(1)}B`} delay={0.15} />
      </div>

      <motion.div
        className="section-header"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.5 }}
      >
        Global Overview
      </motion.div>
      <p className="section-subtext">
        Bubble size = total disaster damage 2016-2025. Color = average temperature. Click a bubble to select that city.
      </p>
      <WorldMap
        cities={data.cities}
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
      />
      <TemperatureChart city={selectedCity} />
      <DamageBarChart cities={data.cities} selectedCity={selectedCity} onSelectCity={setSelectedCity} />
      <BoxplotChart cities={data.cities} />
      <CorrelationHeatmap cities={data.cities} />
      <Treemap cities={data.cities} selectedCity={selectedCity} onSelectCity={setSelectedCity} />
      <QuadrantScatter
        cities={data.cities}
        title="Risk Matrix: Heat Anomaly vs High-Damage-Year Probability"
        subtitle="Precomputed XGBoost risk scores, 0 to 1 scale"
        xLabel="Heat Anomaly Risk"
        yLabel="High-Damage-Year Probability"
        xAccessor={(c) => c.riskScores.heatAnomalyRisk}
        yAccessor={(c) => c.riskScores.highDamageYearProbability}
        xDivider={0.5}
        yDivider={0.5}
        xTooltipFormat={(v) => v.toFixed(2)}
        yTooltipFormat={(v) => v.toFixed(2)}
        quadrantLabels={{
          topLeft: "Low Heat / High Damage Prob",
          topRight: "High Heat / High Damage Prob",
          bottomLeft: "Low Heat / Low Damage Prob",
          bottomRight: "High Heat / Low Damage Prob",
        }}
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
      />
      <QuadrantScatter
        cities={data.cities}
        title="Risk Matrix: Avg Temperature vs Total Damage"
        subtitle="Raw observed values, dividers at dataset median"
        xLabel="Avg Temperature (°C)"
        yLabel="Total Disaster Damage"
        xAccessor={(c) => c.avgTempOverall}
        yAccessor={(c) => c.totalDisasterDamage}
        xDivider={[...data.cities].sort((a,b) => a.avgTempOverall - b.avgTempOverall)[Math.floor(data.cities.length/2)].avgTempOverall}
        yDivider={[...data.cities].sort((a,b) => a.totalDisasterDamage - b.totalDisasterDamage)[Math.floor(data.cities.length/2)].totalDisasterDamage}
        xTooltipFormat={(v) => `${v.toFixed(1)}°C`}
        yTooltipFormat={(v) => `$${(v/1e9).toFixed(2)}B`}
        yTickFormat={(v) => `$${(v/1e9).toFixed(0)}B`}
        quadrantLabels={{
          topLeft: "Cooler / Higher Damage",
          topRight: "Warmer / Higher Damage",
          bottomLeft: "Cooler / Lower Damage",
          bottomRight: "Warmer / Lower Damage",
        }}
        selectedCity={selectedCity}
        onSelectCity={setSelectedCity}
      />
      <HumanitarianScatter cities={data.cities} selectedCity={selectedCity} onSelectCity={setSelectedCity} />
      <KeyFindings keyFindings={data.keyFindings} cities={data.cities} selectedCity={selectedCity} onSelectCity={setSelectedCity} />
    </div>
  )
}

export default App
