 import ReactECharts from 'echarts-for-react'
 export default function ScatterTrend() {
   const data = [[150, 82], [155, 84], [160, 86], [165, 88], [170, 89], [175, 91], [180, 92], [185, 90], [190, 88], [195, 85], [200, 83]]
   const option = {
     title: { text: 'Response Trend: Temperature vs Yield', left: 'center', textStyle: { fontSize: 14 } },
     xAxis: { type: 'value', name: 'Temperature (°C)' },
     yAxis: { type: 'value', name: 'Yield (%)' },
     series: [
       { type: 'scatter', data, symbolSize: 8, itemStyle: { color: '#3b82f6' } },
       { type: 'line', data, smooth: true, lineStyle: { color: '#93c5fd', width: 2 }, symbol: 'none' },
     ],
     grid: { bottom: 50, left: 60 },
     tooltip: { trigger: 'item', formatter: (p: any) => `Temp: ${p.data[0]}°C<br/>Yield: ${p.data[1]}%` },
   }
   return <div className="p-4 rounded-xl border border-border bg-bg-primary">
     <ReactECharts option={option} style={{ height: 280 }} />
   </div>
 }
