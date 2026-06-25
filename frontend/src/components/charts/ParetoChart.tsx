 import ReactECharts from 'echarts-for-react'
 export default function ParetoChart() {
   const categories = ['Temp', 'Pressure', 'Time', 'pH', 'Speed', 'Other']
   const values = [42, 35, 28, 15, 8, 5]
   const total = values.reduce((a, b) => a + b, 0)
   let cumSum = 0; const cumPct = values.map((v) => { cumSum += v; return ((cumSum / total) * 100).toFixed(1) })
   const option = {
     title: { text: 'Pareto Chart', left: 'center', textStyle: { fontSize: 14 } },
     xAxis: { type: 'category', data: categories },
     yAxis: [{ type: 'value', name: 'Effect Size' }, { type: 'value', name: 'Cumulative %', max: 100 }],
     series: [
       { type: 'bar', data: values, itemStyle: { color: '#3b82f6' } },
       { type: 'line', yAxisIndex: 1, data: cumPct, symbol: 'circle', lineStyle: { color: '#ef4444' } },
     ],
     grid: { bottom: 50 },
   }
   return <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
     <ReactECharts option={option} style={{ height: 280 }} />
   </div>
 }
