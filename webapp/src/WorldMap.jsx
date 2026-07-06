import { useState } from 'react'
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps'
import { motion, AnimatePresence } from 'framer-motion'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

function tempToColor(temp, vmin = 10, vmax = 30) {
  const t = Math.max(0, Math.min(1, (temp - vmin) / (vmax - vmin)))
  const r = Math.round(60 + t * 195)
  const g = Math.round(120 + (1 - Math.abs(t - 0.5) * 2) * 90)
  const b = Math.round(240 - t * 190)
  return `rgb(${r}, ${g}, ${b})`
}

export default function WorldMap({ cities, onSelectCity, selectedCity }) {
  const [hovered, setHovered] = useState(null)

  const maxDamage = Math.max(...cities.map((c) => c.totalDisasterDamage), 1)
  const radiusFor = (damage) => 3 + Math.sqrt(damage / maxDamage) * 14

  return (
    <div className="map-container">
      <ComposableMap
        projectionConfig={{ scale: 145 }}
        style={{ width: '100%', height: 'auto' }}
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#12141c"
                stroke="rgba(255,255,255,0.06)"
                strokeWidth={0.5}
                style={{
                  default: { outline: 'none' },
                  hover: { outline: 'none', fill: '#1a1d28' },
                  pressed: { outline: 'none' },
                }}
              />
            ))
          }
        </Geographies>

        {cities.map((city) => {
          const isSelected = selectedCity?.name === city.name
          const isHovered = hovered === city.name
          return (
            <Marker
              key={city.name}
              coordinates={[city.lon, city.lat]}
              onClick={() => onSelectCity(city)}
              onMouseEnter={() => setHovered(city.name)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}
            >
              <motion.circle
                r={radiusFor(city.totalDisasterDamage)}
                fill={tempToColor(city.avgTempOverall)}
                fillOpacity={isSelected ? 0.9 : 0.6}
                stroke={isSelected ? '#34D399' : 'rgba(255,255,255,0.3)'}
                strokeWidth={isSelected ? 2 : 0.5}
                initial={{ scale: 0, opacity: 0 }}
                animate={{
                  scale: isHovered ? 1.3 : 1,
                  opacity: 1,
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              />
            </Marker>
          )
        })}
      </ComposableMap>

      <AnimatePresence>
        {hovered && (
          <motion.div
            className="map-tooltip"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.15 }}
          >
            {(() => {
              const c = cities.find((c) => c.name === hovered)
              return (
                <>
                  <strong>{c.name}, {c.country}</strong>
                  <div>Avg temp: {c.avgTempOverall.toFixed(1)}°C</div>
                  <div>Total damage: ${(c.totalDisasterDamage / 1e9).toFixed(2)}B</div>
                </>
              )
            })()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
