import ReactECharts from 'echarts-for-react'

interface Props {
  categories?: string[]
  values?: number[]
  cumulative?: number[]
}

export default function ParetoChart({ categories = [], values = [], cumulative = [] }: Props) {
  const hasData = categories.length > 0
  const cats = hasData ? categories : ['—']
  const vals = hasData ? values : [0]
  const cum = hasData ? cumulative.map(v => String(v)) : ['0']
  const total = values.reduce((a, b) => a + b, 0)
  let cumSum = 0; const cumPct = values.map((v) => { cumSum += v; return ((cumSum / total) * 100).toFixed(1) })
  const displayCum = hasData ? cumPct : ['0']

  const option = {
    title: { text: 'Pareto Chart', left: 'center', textStyle: { fontSize: 14 } },
    xAxis: { type: 'category', data: cats },
    yAxis: [{ type: 'value', name: 'Effect Size' }, { type: 'value', name: 'Cumulative %', max: 100 }],
    series: [
      { type: 'bar', data: vals, itemStyle: { color: hasData ? '#3b82f6' : '#e5e7eb' } },
      ...(hasData ? [{ type: 'line' as const, yAxisIndex: 1, data: displayCum, symbol: 'circle' as const, lineStyle: { color: '#ef4444' } }] : []),
    ],
    grid: { bottom: 50 },
  }
  const emptyOverlay = !hasData ? (
    <div className="absolute inset-0 flex items-center justify-center z-10" style={{ height: 280 }}>
      <span className="text-xs text-text-muted bg-bg-primary/80 px-3 py-1 rounded">Complete analysis to see Pareto chart</span>
    </div>
  ) : null
  return (
    <div className="p-4 rounded-xl border border-border bg-bg-primary relative">
      {emptyOverlay}
      <ReactECharts option={option} style={{ height: 280, opacity: hasData ? 1 : 0.3 }} />
    </div>
  )
}
