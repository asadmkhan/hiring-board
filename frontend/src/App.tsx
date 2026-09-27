import { useState } from 'react'
import ApplicationDetail from './components/ApplicationDetail'
import ApplicationList from './components/ApplicationList'

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <main>
      <h1>Hiring Board</h1>
      <div className="layout">
        <section>
          <ApplicationList selectedId={selectedId} refreshKey={refreshKey} onSelect={setSelectedId} />
        </section>
        {selectedId && (
          <ApplicationDetail
            key={selectedId}
            id={selectedId}
            onChanged={() => setRefreshKey((n) => n + 1)}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>
    </main>
  )
}
