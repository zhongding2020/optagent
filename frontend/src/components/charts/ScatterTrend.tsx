import ReactECharts from 'echarts-for-react'

interface Props {
  x?: number[]
  y?: number[]
}

export default function ScatterTrend({ x = [], y = [] }: Props) {
  const hasData = x.length > 0 && y.length > 0
  const points = hasData ? x.map((xi, i) => [xi, y[i]]) : [[0, 0]]
  const xName = 'Parameter'
  const yName = 'Response'

  const option = {
    title: { text: hasData ? 'Response Trend' : 'Response Trend (No Data)', left: 'center', textStyle: { fontSize: 14 } },
    xAxis: { type: 'value', name: xName },
    yAxis: { type: 'value', name: yName },
    series: [
      { type: 'scatter', data: points, symbolSize: hasData ? 8 : 0, itemStyle: { color: hasData ? '#3b82f6' : '#e5e7eb' } },
      ...(hasData ? [{ type: 'line' as const, data: points, smooth: true, lineStyle: { color: '#93c5fd', width: 2 }, symbol: 'none' as const }] : []),
    ],
    grid: { bottom: 50, left: 60 },
    tooltip: { trigger: 'item', formatter: hasData ? (p: any) => `${xName}: ${p.data[0]}<br/>${yName}: ${p.data[1]}` : undefined },
  }
  const emptyOverlay = !hasData ? (
    <div className="absolute inset-0 flex items-center justify-center z-10" style={{ height: 280 }}>
      <span className="text-xs text-text-muted bg-bg-primary/80 px-3 py-1 rounded">Collect experiment data to see trends</span>
    </div>
  ) : null
  return (
    <div className="p-4 rounded-xl border border-border bg-bg-primary relative">
      {emptyOverlay}
      <ReactECharts option={option} style={{ height: 280, opacity: hasData ? 1 : 0.3 }} />
    </div>
  )
}
