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
     <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', maxWidth: 1200, margin: '0 auto' }}>
       <div style={{ marginBottom: 20 }}>
         <a href={`/sessions/${id}`} style={{ color: '#666', textDecoration: 'none', fontSize: 14 }}>&larr; Back to session</a>
         <h1 style={{ fontSize: 20, fontWeight: 600, margin: '4px 0' }}>Analysis</h1>
       </div>
       <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
         <FactorRankBar />
         <ParetoChart />
         <CorrelationHeatmap />
         <ScatterTrend />
       </div>
       <div style={{ marginTop: 16 }}>
         <DesignMatrixTable />
       </div>
     </div>
   )
 }
