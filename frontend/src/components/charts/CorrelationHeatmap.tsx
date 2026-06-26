import ReactECharts from 'echarts-for-react'

interface Props {
  factors?: string[]
  values?: number[][]
}

export default function CorrelationHeatmap({ factors = [], values = [] }: Props) {
  const hasData = factors.length > 0 && values.length > 0
  const f = hasData ? factors : ['—']
  const matrix = hasData ? values : [[0]]
  const data = matrix.flatMap((row, i) => row.map((val, j) => [i, j, val]))

  const option = {
    title: { text: 'Correlation Heatmap', left: 'center', textStyle: { fontSize: 14 } },
    xAxis: { type: 'category', data: f, splitArea: { show: true } },
    yAxis: { type: 'category', data: f, splitArea: { show: true } },
    visualMap: { min: hasData ? -1 : 0, max: 1, inRange: { color: ['#ef4444', '#fff', '#22c55e'] }, top: 40 },
    series: [{ type: 'heatmap', data, label: { show: hasData, formatter: (p: any) => p.data[2].toFixed(1) } }],
    grid: { top: 60 },
  }
  const emptyOverlay = !hasData ? (
    <div className="absolute inset-0 flex items-center justify-center z-10" style={{ height: 320 }}>
      <span className="text-xs text-text-muted bg-bg-primary/80 px-3 py-1 rounded">Complete analysis to see correlations</span>
    </div>
  ) : null
  return (
    <div className="p-4 rounded-xl border border-border bg-bg-primary relative">
      {emptyOverlay}
      <ReactECharts option={option} style={{ height: 320, opacity: hasData ? 1 : 0.3 }} />
    </div>
  )
}
