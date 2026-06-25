import { useParams, useNavigate } from 'react-router-dom'
import FactorRankBar from '../components/charts/FactorRankBar'
import CorrelationHeatmap from '../components/charts/CorrelationHeatmap'
import ParetoChart from '../components/charts/ParetoChart'
import DesignMatrixTable from '../components/charts/DesignMatrixTable'
import ScatterTrend from '../components/charts/ScatterTrend'

export default function Analysis() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <div className="max-w-6xl mx-auto px-8 py-8">
      <h1 className="text-xl font-bold text-text-primary mb-6">Analysis</h1>
      <div className="grid grid-cols-2 gap-4">
        <FactorRankBar />
        <ParetoChart />
        <CorrelationHeatmap />
        <ScatterTrend />
      </div>
      <div className="mt-4">
        <DesignMatrixTable />
      </div>
    </div>
  )
}
