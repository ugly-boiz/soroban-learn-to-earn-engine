import React, {useState} from 'react'

export default function App(){
  const [pred, setPred] = useState(null)
  const callPredict = async () => {
    const res = await fetch('http://localhost:8000/predict', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({batch_size:4})})
    const j = await res.json()
    setPred(j.predictions)
  }
  return (
    <div style={{padding:20}}>
      <h1>ConsSparse demo</h1>
      <button onClick={callPredict}>Run Predict (demo)</button>
      <pre>{JSON.stringify(pred, null, 2)}</pre>
    </div>
  )
}
