 import ReactECharts from 'echarts-for-react'
 export default function FactorRankBar() {
   const option = {
     title: { text: 'Factor Importance Ranking', left: 'center', textStyle: { fontSize: 14 } },
     xAxis: { type: 'category', data: ['Temp', 'Pressure', 'Time', 'pH', 'Speed'], axisLabel: { rotate: 30 } },
     yAxis: { type: 'value', name: 'Effect Size' },
     series: [{ type: 'bar', data: [42, 35, 28, 15, 8], itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] } }],
     grid: { bottom: 60 },
   }
   return <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
     <ReactECharts option={option} style={{ height: 280 }} />
   </div>
 }
