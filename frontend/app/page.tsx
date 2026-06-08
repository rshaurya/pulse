'use client'

import { useState, FormEvent } from 'react'
import { Send, Zap, Shield, Brain, ArrowRight } from 'lucide-react'

type Status = 'idle' | 'loading' | 'success' | 'error'

// ─── Animated PULSE Logo ─────────────────────────────────────────────────────
function PulseLogo() {
  const letters = ['P', 'U', 'L', 'S', 'E']
  return (
    <h1
      aria-label="PULSE"
      className="select-none leading-none font-black tracking-tighter"
      style={{
        fontFamily: 'var(--font-space-grotesk)',
        fontSize: 'clamp(5rem, 18vw, 10rem)',
        whiteSpace: 'nowrap',
      }}
    >
      {letters.map((char, i) => (
        <span
          key={char}
          className="letter-reveal"
          style={{
            animationDelay: `${0.1 + i * 0.08}s`,
            background: 'linear-gradient(145deg, #ffffff 10%, #a5b4fc 45%, #4D4DFF 75%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          {char}
        </span>
      ))}
    </h1>
  )
}

// ─── Feature pills ────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: Brain,  label: 'LLM-Powered',  sub: 'Groq inference' },
  { icon: Zap,    label: 'Real-time',    sub: 'Tavily crawling' },
  { icon: Shield, label: 'Self-hosted',  sub: 'Your data only' },
]

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const [email, setEmail]   = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [hint, setHint]     = useState('')

    const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!email) return

    setStatus('loading')
    
    try {
      // The Real API Call to your FastAPI backend
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/api/auth/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: email }), // Ensure we send JSON!
      })

      if (response.ok) {
        // Only show success if the backend actually sent the email!
        setStatus('success')
      } else {
        // If FastAPI throws a 400 or 500 error
        console.error("Backend refused the request. Status:", response.status)
        setStatus('error')
      }
    } catch (error) {
      // If the backend is turned off, or CORS blocks it
      console.error("Network or CORS Error:", error)
      setStatus('error')
    }
  }

  const isDisabled = status === 'loading' || status === 'success'

  return (
    <main className="relative min-h-dvh flex flex-col items-center justify-center overflow-hidden grid-bg">

      {/* ── Depth gradient ── */}
      <div className="pointer-events-none absolute inset-0 radial-depth" />

      {/* ── Ambient glow orbs ── */}
      <div
        className="pointer-events-none absolute -left-56 top-1/3 h-96 w-96 rounded-full blur-3xl"
        style={{ background: 'rgba(77, 77, 255, 0.12)' }}
      />
      <div
        className="pointer-events-none absolute -right-56 bottom-1/4 h-80 w-80 rounded-full blur-3xl"
        style={{ background: 'rgba(255, 107, 107, 0.09)' }}
      />

      {/* ── Scanline ── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="scanline absolute h-px w-full"
          style={{
            background:
              'linear-gradient(90deg, transparent 0%, rgba(77,77,255,0.6) 50%, transparent 100%)',
          }}
        />
      </div>

      {/* ── Content ── */}
      <div className="relative z-10 flex w-full flex-col items-center px-6">

        {/* System status badge */}
        <div
          className="animate-entrance mb-10"
          style={{ animationDelay: '0.05s' }}
        >
          <span
            className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]"
            style={{
              fontFamily: 'var(--font-space-grotesk)',
              background: 'rgba(77,77,255,0.1)',
              border: '1px solid rgba(77,77,255,0.28)',
              color: '#818cff',
            }}
          >
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#4D4DFF]" />
            System Online
          </span>
        </div>

        {/* Logo — unconstrained so letters never wrap */}
        <PulseLogo />

        {/* Everything below the logo is constrained to a readable column width */}
        <div className="flex w-full max-w-sm flex-col items-center">

        {/* Tagline */}
        <p
          className="animate-entrance mt-4 mb-12 max-w-[260px] text-center text-[13px] leading-relaxed"
          style={{
            animationDelay: '0.52s',
            fontFamily: 'var(--font-inter)',
            color: 'rgba(255,255,255,0.36)',
            letterSpacing: '0.04em',
          }}
        >
          Personalized AI knowledge engine.
          <br />
          Headless. Autonomous. Always&nbsp;on.
        </p>

        {/* ── Magic Link Form ── */}
        <form
          onSubmit={handleSubmit}
          className="animate-entrance w-full"
          style={{ animationDelay: '0.62s' }}
        >
          {/* Email input */}
          <div
            className="pulse-input mb-3 flex items-center gap-3 rounded-xl px-4 py-3.5 transition-all duration-300"
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.09)',
            }}
          >
            <Send
              size={15}
              style={{ color: 'rgba(77,77,255,0.55)', flexShrink: 0 }}
            />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              disabled={isDisabled}
              className="flex-1 bg-transparent text-[14px] text-white placeholder-white/20 focus:outline-none disabled:cursor-not-allowed"
              style={{ fontFamily: 'var(--font-inter)' }}
            />
          </div>

          {/* CTA button */}
          <button
            type="submit"
            disabled={isDisabled}
            className={`cta-glow flex w-full items-center justify-center gap-2 rounded-xl py-4 text-[13px] font-bold uppercase tracking-[0.14em] transition-all duration-300 disabled:cursor-not-allowed ${
              status === 'success' ? 'opacity-75' : 'hover:brightness-110 active:scale-[0.98]'
            }`}
            style={{
              fontFamily: 'var(--font-space-grotesk)',
              background:
                status === 'success'
                  ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                  : 'linear-gradient(135deg, #4D4DFF 0%, #6e6eff 100%)',
            }}
          >
            {status === 'loading' ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/25 border-t-white" />
                Transmitting…
              </>
            ) : status === 'success' ? (
              'Link Dispatched ✓'
            ) : (
              <>
                Send Magic Link
                <ArrowRight size={14} />
              </>
            )}
          </button>

          {/* Hint message */}
          {hint && (
            <p
              className="animate-entrance mt-3 text-center text-[12px]"
              style={{
                fontFamily: 'var(--font-inter)',
                color: status === 'error' ? '#FF6B6B' : 'rgba(255,255,255,0.42)',
              }}
            >
              {hint}
            </p>
          )}
        </form>

        {/* ── Feature row ── */}
        <div
          className="animate-entrance mt-16 grid w-full grid-cols-3 gap-4"
          style={{ animationDelay: '0.76s' }}
        >
          {FEATURES.map(({ icon: Icon, label, sub }) => (
            <div key={label} className="flex flex-col items-center gap-2 text-center">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-lg"
                style={{
                  background: 'rgba(77,77,255,0.09)',
                  border: '1px solid rgba(77,77,255,0.22)',
                }}
              >
                <Icon size={15} style={{ color: '#6e6eff' }} />
              </div>
              <div>
                <p
                  className="text-[11px] font-semibold text-white/55"
                  style={{ fontFamily: 'var(--font-space-grotesk)' }}
                >
                  {label}
                </p>
                <p
                  className="text-[10px] text-white/22"
                  style={{ fontFamily: 'var(--font-inter)' }}
                >
                  {sub}
                </p>
              </div>
            </div>
          ))}
        </div>
        {/* ── end max-w-sm inner column ── */}
        </div>
      </div>
      {/* ── Bottom status bar ── */}
      <footer
        className="animate-entrance absolute bottom-6 left-0 right-0 flex justify-center"
        style={{ animationDelay: '0.9s' }}
      >
        <span
          className="text-[10px] uppercase tracking-[0.2em]"
          style={{
            fontFamily: 'var(--font-space-grotesk)',
            color: 'rgba(255,255,255,0.13)',
          }}
        >
          PULSE v1.0 · Secure Channel · AES-256
        </span>
      </footer>
    </main>
  )
}
