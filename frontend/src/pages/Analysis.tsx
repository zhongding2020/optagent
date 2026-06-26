import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'
import FactorRankBar from '../components/charts/FactorRankBar'
import CorrelationHeatmap from '../components/charts/CorrelationHeatmap'
import ParetoChart from '../components/charts/ParetoChart'
import DesignMatrixTable from '../components/charts/DesignMatrixTable'
import ScatterTrend from '../components/charts/ScatterTrend'

export default function Analysis() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.getAnalysisData(id)
      .then((res: any) => {
        setAnalysisData(res?.data || {})
        setLoading(false)
      })
      .catch((e) => {
        setError(e.message)
        setLoading(false)
      })
  }, [id])

  const d = analysisData || {}
  const factorData: { name: string; value: number }[] = d.factor_importance || []
  const corrFactors: string[] = d.correlation?.factors || []
  const corrValues: number[][] = d.correlation?.values || []
  const paretoCats: string[] = d.pareto?.categories || []
  const paretoVals: number[] = d.pareto?.values || []
  const paretoCum: number[] = d.pareto?.cumulative || []
  const scatterX: number[] = d.scatter?.x || []
  const scatterY: number[] = d.scatter?.y || []

  return (
    <div className="max-w-6xl mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-text-primary">Analysis</h1>
        <span className={`text-xs px-2 py-0.5 rounded-full ${loading ? 'bg-warning/20 text-warning' : 'bg-success/20 text-success'}`}>
          {loading ? 'Loading...' : error ? 'Error' : 'Ready'}
        </span>
      </div>
      {loading ? (
        <div className="flex items-center justify-center h-64 text-text-muted text-sm">Loading analysis data...</div>
      ) : error ? (
        <div className="flex items-center justify-center h-64 text-danger text-sm">Error: {error}</div>
      ) : (
      <>
      <div className="grid grid-cols-2 gap-4">
        <FactorRankBar data={factorData} />
        <ParetoChart categories={paretoCats} values={paretoVals} cumulative={paretoCum} />
        <CorrelationHeatmap factors={corrFactors} values={corrValues} />
        <ScatterTrend x={scatterX} y={scatterY} />
      </div>
      <div className="mt-4">
        <DesignMatrixTable />
      </div>
      </>
      )}
    </div>
  )
}
