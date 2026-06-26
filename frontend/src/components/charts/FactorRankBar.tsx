import ReactECharts from 'echarts-for-react'

interface Props {
  data?: { name: string; value: number }[]
}

export default function FactorRankBar({ data = [] }: Props) {
  const hasData = data.length > 0
  const names = hasData ? data.map(d => d.name) : ['—']
  const values = hasData ? data.map(d => d.value) : [0]
  const color = hasData ? '#3b82f6' : '#e5e7eb'

  const option = {
    title: { text: 'Factor Importance Ranking', left: 'center', textStyle: { fontSize: 14 } },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: hasData ? 30 : 0 } },
    yAxis: { type: 'value', name: 'Effect Size' },
    series: [{ type: 'bar', data: values, itemStyle: { color, borderRadius: [4, 4, 0, 0] } }],
    grid: { bottom: 60 },
  }
  return (
    <div className="p-4 rounded-xl border border-border bg-bg-primary">
      {hasData ? (
        <ReactECharts option={option} style={{ height: 280 }} />
      ) : (
        <div className="relative">
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ height: 280 }}>
            <span className="text-xs text-text-muted bg-bg-primary/80 px-3 py-1 rounded">Complete the workflow to see factor analysis</span>
          </div>
          <ReactECharts option={option} style={{ height: 280, opacity: 0.3 }} />
        </div>
      )}
    </div>
  )
}
