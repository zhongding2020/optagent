 const thClass = "px-3 py-2 text-left border-b-2 border-border font-semibold text-xs text-text-secondary uppercase tracking-wider"
 const tdClass = "px-3 py-2 border-b border-border text-sm text-text-primary"
 
 export default function DesignMatrixTable() {
   const runs = [
     { run: 1, temp: 150, pressure: 3, time: 30 }, { run: 2, temp: 150, pressure: 5, time: 60 },
     { run: 3, temp: 200, pressure: 3, time: 60 }, { run: 4, temp: 200, pressure: 5, time: 30 },
   ]
   return (
     <div className="p-4 rounded-xl border border-border bg-bg-primary">
       <h3 className="text-sm font-semibold text-text-primary mb-3">DOE Design Matrix</h3>
       <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
         <thead><tr className="bg-bg-secondary">
           <th className={thClass}>Run</th><th className={thClass}>Temperature (&deg;C)</th>
           <th className={thClass}>Pressure (bar)</th><th className={thClass}>Time (min)</th>
         </tr></thead>
         <tbody>{runs.map((r) => (
           <tr key={r.run}><td className={tdClass}>{r.run}</td><td className={tdClass}>{r.temp}</td>
           <td className={tdClass}>{r.pressure}</td><td className={tdClass}>{r.time}</td></tr>
         ))}</tbody>
       </table>
     </div>
   )
 }
