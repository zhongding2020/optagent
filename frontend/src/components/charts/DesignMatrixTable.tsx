 const thStyle: React.CSSProperties = { padding: '8px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 600 }
 const tdStyle: React.CSSProperties = { padding: '8px 12px', borderBottom: '1px solid #e5e7eb' }
 
 export default function DesignMatrixTable() {
   const runs = [
     { run: 1, temp: 150, pressure: 3, time: 30 }, { run: 2, temp: 150, pressure: 5, time: 60 },
     { run: 3, temp: 200, pressure: 3, time: 60 }, { run: 4, temp: 200, pressure: 5, time: 30 },
   ]
   return (
     <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
       <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#374151' }}>DOE Design Matrix</h3>
       <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
         <thead><tr style={{ background: '#f9fafb' }}>
           <th style={thStyle}>Run</th><th style={thStyle}>Temperature (&deg;C)</th>
           <th style={thStyle}>Pressure (bar)</th><th style={thStyle}>Time (min)</th>
         </tr></thead>
         <tbody>{runs.map((r) => (
           <tr key={r.run}><td style={tdStyle}>{r.run}</td><td style={tdStyle}>{r.temp}</td>
           <td style={tdStyle}>{r.pressure}</td><td style={tdStyle}>{r.time}</td></tr>
         ))}</tbody>
       </table>
     </div>
   )
 }
