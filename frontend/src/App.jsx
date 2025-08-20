import { useMemo, useState } from 'react'

const MODES = [
  { value: 'summarize', label: 'Summarize' },
  { value: 'rephrase', label: 'Rephrase' },
  { value: 'extract_json', label: 'Extract JSON' },
  { value: 'classify', label: 'Classify sentiment' },
]

const TONES = [
  { value: 'casual', label: 'Casual' },
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
]

function App() {
  const [text, setText] = useState('')
  const [mode, setMode] = useState('summarize')
  const [tone, setTone] = useState('casual')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState('')
  const [isJsonRendered, setIsJsonRendered] = useState(false)
  const [usage, setUsage] = useState({ prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 })

  const max = 5000
  const len = text.length
  const overLimit = len > max
  const valid = len >= 1 && !overLimit && !(mode === 'rephrase' && !tone)
  const showTone = mode === 'rephrase'
  const resultClass = useMemo(() => (isJsonRendered ? 'mono' : ''), [isJsonRendered])

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!valid) return
    setError('')
    setBusy(true)
    setResult('')
    setIsJsonRendered(false)

    const payload = { mode, text }
    if (mode === 'rephrase') payload.tone = tone

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) {
        const message = data?.detail || 'Request failed. Please try again.'
        throw new Error(message)
      }

      let rendered = ''
      let jsonRendered = false
      if (mode === 'extract_json') {
        try {
          if (typeof data.result === 'string') {
            const obj = JSON.parse(data.result)
            rendered = JSON.stringify(obj, null, 2)
            jsonRendered = true
          } else {
            rendered = JSON.stringify(data.result, null, 2)
            jsonRendered = true
          }
        } catch (_) {
          rendered = String(data.result)
          jsonRendered = false
        }
      } else {
        rendered = String(data.result)
      }

      setResult(rendered)
      setIsJsonRendered(jsonRendered)
      setUsage({
        prompt_tokens: data?.usage?.prompt_tokens ?? 0,
        completion_tokens: data?.usage?.completion_tokens ?? 0,
        total_tokens: data?.usage?.total_tokens ?? 0,
      })
    } catch (err) {
      setError(err?.message || 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(result)
    } catch (_) { }
  }

  return (
    <>
      {/* Usage floating */}
      {result && (
        <div className="fixed top-4 right-4 bg-card/90 border border-border rounded-xl px-3 py-2 shadow-glass min-w-40">
          <div className="flex items-center justify-between gap-3 text-sm"><span className="text-muted">Prompt</span><span>{usage.prompt_tokens}</span></div>
          <div className="flex items-center justify-between gap-3 text-sm mt-1"><span className="text-muted">Completion</span><span>{usage.completion_tokens}</span></div>
          <div className="flex items-center justify-between gap-3 text-sm mt-1"><span className="text-muted">Total</span><span>{usage.total_tokens}</span></div>
        </div>
      )}

      <div className="max-w-3xl mx-auto mt-10 mb-10 p-6 bg-card/60 border border-border rounded-2xl backdrop-blur-xs shadow-glass flex flex-col overflow-hidden max-h-[calc(100vh-5rem)]">
        <h1 className="text-2xl font-semibold mb-4">MindTech OpenAI Integration App</h1>

        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label htmlFor="text" className="block text-sm text-muted mb-1">Text (1-5000 chars)</label>
            <textarea
              id="text"
              name="text"
              required
              minLength={1}
              maxLength={max}
              placeholder="Paste text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="w-full min-h-40 resize-y bg-card text-text border border-border rounded-xl p-3 outline-none focus:ring-2 focus:ring-accent/60"
            />
            <div className={`mt-1 text-xs ${overLimit ? 'text-red-400' : 'text-muted'}`}>{len} / {max}</div>
          </div>

          <div className={`${showTone ? 'grid grid-cols-1 sm:grid-cols-2' : 'grid grid-cols-1'} gap-3`}>
            <div>
              <label htmlFor="mode" className="block text-sm text-muted mb-1">Mode</label>
              <select
                id="mode"
                name="mode"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                required
                className="w-full bg-card text-text border border-border rounded-xl p-2.5 pr-12 outline-none focus:ring-2 focus:ring-accent/60 select-chev"
              >
                {MODES.map(m => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            {showTone && (
              <div>
                <label htmlFor="tone" className="block text-sm text-muted mb-1">Tone</label>
                <select
                  id="tone"
                  name="tone"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full bg-card text-text border border-border rounded-xl p-2.5 pr-12 outline-none focus:ring-2 focus:ring-accent/60 select-chev"
                >
                  {TONES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <button
            type="submit"
            id="submit-btn"
            disabled={!valid || busy}
            className="inline-flex items-center justify-center px-4 py-2 rounded-xl font-semibold bg-accent text-slate-900 disabled:opacity-60"
          >
            {busy ? 'Running…' : 'Run'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-xl border border-red-400/40 bg-red-900/40 text-sm">{error}</div>
        )}

        {result && (
          <div className="mt-5 border border-border rounded-2xl bg-card flex-1 min-h-0 overflow-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/70">
              <h2 className="text-lg font-medium">Result</h2>
              <button
                id="copy-btn"
                type="button"
                onClick={copyToClipboard}
                title="Copy result"
                className="px-3 py-1.5 rounded-lg bg-accent text-slate-900 font-semibold"
              >
                Copy
              </button>
            </div>
            <pre id="result" className={`${resultClass} p-4 whitespace-pre-wrap break-words`}>{result}</pre>
          </div>
        )}
      </div>
    </>
  )
}

export default App
