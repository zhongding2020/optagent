import ReactECharts from 'echarts-for-react'

interface Props {
  chartType: string
  data: Record<string, any>
  label?: string
}

export default function AnalysisChart({ chartType, data, label }: Props) {
  if (!data || Object.keys(data).length === 0) return null

  // ── Factor Importance ────────────────────────────────────────────────
  if (chartType === 'factor_importance' && data.ranked_factors) {
    const factors = data.ranked_factors as { factor: string; importance_pct: number }[]
    const option = {
      title: { text: label || 'Factor Importance', left: 'center', textStyle: { fontSize: 13 } },
      xAxis: { type: 'category', data: factors.map(f => f.factor), axisLabel: { rotate: 20, fontSize: 11 } },
      yAxis: { type: 'value', name: 'Importance %', max: 100 },
      series: [{
        type: 'bar', data: factors.map(f => f.importance_pct),
        itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: (p: any) => `${p.value}%`, fontSize: 11 },
      }],
      grid: { bottom: 40, top: 40, left: 50, right: 20 },
    }
    return <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
      <ReactECharts option={option} style={{ height: 220 }} />
    </div>
  }

  // ── Correlation Heatmap ──────────────────────────────────────────────
  if (chartType === 'correlation_analysis' && data.factors && data.correlation_matrix) {
    const f = data.factors as string[]
    const m = data.correlation_matrix as number[][]
    const cells = m.flatMap((row, i) => row.map((val, j) => [i, j, val]))
    const option = {
      title: { text: label || 'Correlation Heatmap', left: 'center', textStyle: { fontSize: 13 } },
      xAxis: { type: 'category', data: f, splitArea: { show: true } },
      yAxis: { type: 'category', data: f, splitArea: { show: true } },
      visualMap: { min: -1, max: 1, inRange: { color: ['#ef4444', '#fff', '#22c55e'] }, top: 35, right: 5, calculable: true },
      series: [{ type: 'heatmap', data: cells, label: { show: true, formatter: (p: any) => p.data[2].toFixed(2), fontSize: 10 } }],
      grid: { top: 45, left: 60, right: 60 },
    }
    return <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
      <ReactECharts option={option} style={{ height: 240 }} />
    </div>
  }

  // ── Pareto Analysis ──────────────────────────────────────────────────
  if (chartType === 'pareto_analysis' && data.items) {
    const items = data.items as { category: string; value: number; cumulative_pct: number; percentage: number }[]
    const barData = items.map(i => i.value)
    const lineData = items.map(i => i.cumulative_pct)
    const cats = items.map(i => i.category)
    const option = {
      title: { text: label || 'Pareto Analysis', left: 'center', textStyle: { fontSize: 13 } },
      xAxis: { type: 'category', data: cats, axisLabel: { rotate: 20, fontSize: 10 } },
      yAxis: [
        { type: 'value', name: 'Value' },
        { type: 'value', name: 'Cumulative %', max: 100 },
      ],
      series: [
        { type: 'bar', data: barData, itemStyle: { color: '#3b82f6' } },
        { type: 'line', yAxisIndex: 1, data: lineData, symbol: 'circle', lineStyle: { color: '#ef4444' } },
      ],
      grid: { bottom: 40, top: 40 },
    }
    return <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
      <ReactECharts option={option} style={{ height: 220 }} />
    </div>
  }

  // ── Response Surface (RSM) ───────────────────────────────────────────
  if (chartType === 'response_surface' && data.optimal_point) {
    const factors = data.factors as string[]
    const opt = data.optimal_point as Record<string, number>
    return (
      <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
        <h4 className="text-xs font-semibold text-text-secondary mb-2">{label || 'Response Surface'}</h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 rounded-lg bg-bg-secondary">
            <span className="text-text-muted">R²</span>
            <div className="text-lg font-bold text-accent">{data.r_squared}</div>
          </div>
          <div className="p-2 rounded-lg bg-bg-secondary">
            <span className="text-text-muted">Predicted Optimum</span>
            <div className="text-lg font-bold text-success">{data.predicted_optimum}</div>
          </div>
        </div>
        <div className="mt-2 p-2 rounded-lg bg-bg-secondary text-xs">
          <span className="text-text-muted">Optimal Parameters</span>
          {factors.map(f => (
            <div key={f} className="flex justify-between mt-1">
              <span>{f}</span>
              <span className="font-medium">{opt[f]}</span>
            </div>
          ))}
        </div>
        <details className="mt-2">
          <summary className="text-xs text-text-muted cursor-pointer hover:text-text-secondary">Model Coefficients</summary>
          <div className="mt-1 text-xs space-y-0.5">
            {Object.entries(data.model_coefficients || {}).map(([k, v]) => (
              <div key={k} className="flex justify-between px-1">
                <span className="text-text-muted">{k}</span>
                <span className="font-mono">{(v as number).toFixed(4)}</span>
              </div>
            ))}
          </div>
        </details>
      </div>
    )
  }

  // ── DOE Design Matrix ────────────────────────────────────────────────
  if (chartType === 'design_experiment' && data.design_matrix) {
    const dm = data.design_matrix as { columns: string[]; rows: number[][] }
    const totalRuns = data.total_runs
    return (
      <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold text-text-secondary">{label || 'DOE Design Matrix'}</h4>
          <span className="text-[10px] text-text-muted bg-bg-secondary px-2 py-0.5 rounded">{totalRuns} runs</span>
        </div>
        <div className="overflow-x-auto" style={{ maxHeight: 160 }}>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-bg-secondary">
                <th className="px-2 py-1 border border-border text-left font-medium text-text-secondary">#</th>
                {dm.columns.map(c => <th key={c} className="px-2 py-1 border border-border text-left font-medium text-text-secondary">{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {dm.rows.map((row, i) => (
                <tr key={i} className="hover:bg-bg-hover">
                  <td className="px-2 py-1 border border-border text-text-muted">{i + 1}</td>
                  {row.map((v, j) => (
                    <td key={j} className="px-2 py-1 border border-border font-mono">{v}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  // ── ANOVA ────────────────────────────────────────────────────────────
  if (chartType === 'anova_one_way' && data.groups) {
    const groups = data.groups as Record<string, { mean: number }>
    const names = Object.keys(groups)
    const means = names.map(n => groups[n].mean)
    const sig = data.significant
    const option = {
      title: { text: label || 'ANOVA: Group Means', left: 'center', textStyle: { fontSize: 13 } },
      xAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value', name: 'Mean' },
      series: [{
        type: 'bar', data: means,
        itemStyle: {
          color: (p: any) => sig === true ? (p.value > 0 ? '#22c55e' : '#ef4444') : '#3b82f6',
          borderRadius: [4, 4, 0, 0],
        },
      }],
      graphic: sig !== undefined ? [{
        type: 'text', left: 'center', top: 5,
        style: {
          text: sig ? '✓ Significant (p < 0.05)' : '✗ Not significant',
          fill: sig ? '#22c55e' : '#ef4444',
          fontSize: 11,
        },
      }] : [],
      grid: { bottom: 30, top: 35 },
    }
    return <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
      <ReactECharts option={option} style={{ height: 200 }} />
    </div>
  }

  // ── Fallback: JSON view ──────────────────────────────────────────────
  return (
    <div className="my-2 p-3 rounded-xl border border-border bg-bg-primary">
      <details>
        <summary className="text-xs font-medium text-text-secondary cursor-pointer">
          {label || 'Analysis Result'} (click to view)
        </summary>
        <pre className="mt-2 text-[11px] text-text-muted overflow-x-auto max-h-40">
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  )
}
