 import ReactECharts from 'echarts-for-react'
 export default function CorrelationHeatmap() {
   const factors = ['Temp', 'Pressure', 'Time', 'pH', 'Speed']
   const values = [
     [1.0, 0.3, -0.2, 0.5, 0.1], [0.3, 1.0, 0.4, -0.1, 0.6],
     [-0.2, 0.4, 1.0, 0.2, -0.3], [0.5, -0.1, 0.2, 1.0, 0.0], [0.1, 0.6, -0.3, 0.0, 1.0],
   ]
   const data = values.flatMap((row, i) => row.map((v, j) => [i, j, v]))
   const option = {
     title: { text: 'Correlation Heatmap', left: 'center', textStyle: { fontSize: 14 } },
     xAxis: { type: 'category', data: factors, splitArea: { show: true } },
     yAxis: { type: 'category', data: factors, splitArea: { show: true } },
     visualMap: { min: -1, max: 1, inRange: { color: ['#ef4444', '#fff', '#22c55e'] }, top: 40 },
     series: [{ type: 'heatmap', data, label: { show: true, formatter: (p: any) => p.data[2].toFixed(1) } }],
     grid: { top: 60 },
   }
   return <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
     <ReactECharts option={option} style={{ height: 320 }} />
   </div>
 }
