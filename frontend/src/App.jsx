import React, {useState} from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App(){
  const [pred, setPred] = useState(null)
  const [recordValue, setRecordValue] = useState(42)
  const [chainRes, setChainRes] = useState(null)

  const callPredict = async () => {
    const res = await fetch(`${API_BASE}/predict`, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({batch_size:4})})
    const j = await res.json()
    setPred(j.predictions)
  }

  const recordOnChain = async () => {
    try {
      const res = await fetch(`${API_BASE}/record_on_chain`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ value: Number(recordValue) })
      })
      const j = await res.json()
      setChainRes(j)
    } catch (e) {
      setChainRes({status: 'error', detail: String(e)})
    }
  }

  return (
    <div style={{padding:20}}>
      <h1>ConsSparse demo</h1>
      <button onClick={callPredict}>Run Predict (demo)</button>
      <pre>{JSON.stringify(pred, null, 2)}</pre>

      <hr />
      <h2>Record on Testnet</h2>
      <div>
        <input type="number" value={recordValue} onChange={(e) => setRecordValue(e.target.value)} />
        <button onClick={recordOnChain} style={{marginLeft:8}}>Record to Testnet</button>
      </div>
      <pre>{JSON.stringify(chainRes, null, 2)}</pre>
    </div>
  )
}
