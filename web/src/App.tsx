import { useEffect, useState } from 'react'
import { api } from './data'
import { Overview } from './Overview'
import { Rollout } from './Rollout'
import { Incidents } from './Incidents'
import { Log } from './Log'
import type { Summary } from './types'

function useRoute() {
  const [h, setH] = useState(location.hash || '#/')
  useEffect(() => { const f = () => setH(location.hash || '#/'); addEventListener('hashchange', f); return () => removeEventListener('hashchange', f) }, [])
  return h.slice(2).split('/')
}

export function App() {
  const [page, arg] = useRoute()
  const [s, setS] = useState<Summary | null>(null)
  const [actor, setActor] = useState(() => { try { return localStorage.getItem('second-plant:actor') ?? 'shift engineer' } catch { return 'shift engineer' } })
  useEffect(() => { api.summary().then(setS) }, [])
  useEffect(() => { try { localStorage.setItem('second-plant:actor', actor) } catch { /* ignore */ } }, [actor])
  const tabs: [string, string][] = [['', 'Overview'], ['rollout', 'Rollout to plant B'], ['incidents', 'Deviations'], ['log', 'Decision log']]
  return (
    <>
      <header><div className="wrap">
        <div className="brand">second<span>-</span>plant</div>
        <nav>{tabs.map(([k, l]) => <a key={k} href={`#/${k}`} className={(page || '') === k ? 'on' : ''}>{l}</a>)}</nav>
        <div className="right"><span className="small muted">You:</span><input className="actor" aria-label="Your name" value={actor} onChange={e => setActor(e.target.value)} /></div>
      </div></header>
      <main><div className="wrap">
        {!s ? <p className="muted">Loading…</p> :
          page === 'rollout' ? <Rollout actor={actor} summary={s} /> :
          page === 'incidents' ? <Incidents id={arg} actor={actor} /> :
          page === 'log' ? <Log /> : <Overview s={s} />}
      </div></main>
      <footer><div className="wrap">Data: Tennessee Eastman process (Downs and Vogel 1993; Braatz group data set). Python, FastAPI, PostgreSQL, TypeScript, React, Docker. <a href="https://github.com/vishalbanwari26/second-plant">Source</a></div></footer>
    </>
  )
}
