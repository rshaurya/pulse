'use client'

import { useState, useCallback, useEffect } from 'react'
import { Key, Brain, Save, Zap, LogOut, CheckCircle2, AlertCircle } from 'lucide-react'
import PasswordInput from '@/components/PasswordInput'
import TagInput, { type Tag } from '@/components/TagInput'
import { updateProfile, fetchProfile } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────────────
type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

// ─── Card shell ───────────────────────────────────────────────────────────────
function GlassCard({
  children,
  accentColor = 'indigo',
  className = '',
}: {
  children: React.ReactNode
  accentColor?: 'indigo' | 'coral'
  className?: string
}) {
  const borderColor =
    accentColor === 'indigo'
      ? 'rgba(77,77,255,0.18)'
      : 'rgba(255,107,107,0.18)'

  return (
    <div
      className={`glass rounded-2xl p-6 transition-all duration-300 hover:brightness-105 ${className}`}
      style={{ borderColor }}
    >
      {children}
    </div>
  )
}

// ─── Card header ──────────────────────────────────────────────────────────────
function CardHeader({
  icon: Icon,
  title,
  subtitle,
  accentColor,
}: {
  icon: React.ElementType
  title: string
  subtitle: string
  accentColor: 'indigo' | 'coral'
}) {
  const [bg, border, color] =
    accentColor === 'indigo'
      ? ['rgba(77,77,255,0.12)', 'rgba(77,77,255,0.28)', '#818cff']
      : ['rgba(255,107,107,0.1)', 'rgba(255,107,107,0.28)', '#ff8f8f']

  return (
    <div className="mb-6 flex items-start gap-3">
      <div
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
        style={{ background: bg, border: `1px solid ${border}` }}
      >
        <Icon size={15} style={{ color }} />
      </div>
      <div>
        <h3
          className="text-[14px] font-bold text-white"
          style={{ fontFamily: 'var(--font-space-grotesk)' }}
        >
          {title}
        </h3>
        <p
          className="mt-0.5 text-[12px]"
          style={{ fontFamily: 'var(--font-inter)', color: 'rgba(255,255,255,0.32)' }}
        >
          {subtitle}
        </p>
      </div>
    </div>
  )
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  // ── State ──
  const [groqKey,   setGroqKey]   = useState('')
  const [tavilyKey, setTavilyKey] = useState('')
  const [tags,      setTags]      = useState<Tag[]>([
    { id: '1', label: 'AI Research' },
    { id: '2', label: 'Cybersecurity' },
    { id: '3', label: 'LLM Engineering' },
  ])
  const [isDirty,    setIsDirty]    = useState(false)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [loading,    setLoading]    = useState(true)

  // ── Fetch saved profile on mount ──
  useEffect(() => {
    fetchProfile()
      .then((data) => {
        setTags(data.interests.map((label, i) => ({ id: String(i), label })))
      })
      .catch(() => {/* silently use defaults */})
      .finally(() => setLoading(false))
  }, [])

  // ── Helpers ──
  function markDirty() { setIsDirty(true) }

  const handleAddTag = useCallback((label: string) => {
    setTags((prev) => [...prev, { id: `${Date.now()}-${Math.random()}`, label }])
    markDirty()
  }, [])

  const handleRemoveTag = useCallback((id: string) => {
    setTags((prev) => prev.filter((t) => t.id !== id))
    markDirty()
  }, [])

const handleSave = async () => {
    // 1. Grab the secure user_id from browser memory
    const userId = typeof window !== 'undefined' ? localStorage.getItem('pulse_user_id') : null;

    if (!userId) {
      console.error("No user ID found. Are you logged in?");
      setSaveStatus('error');
      return;
    }

    setSaveStatus('saving');

    try {
      // 2. Transform the Tag objects {id, label} into a clean array of strings
      const stringTags = tags.map((tag: Tag) => tag.label);

      // 3. The PATCH request to your FastAPI container
      const response = await fetch(`http://localhost:8000/api/users/${userId}/settings`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          groq_api_key: groqKey, // Make sure these match your actual state variables!
          tavily_api_key: tavilyKey,
          core_interests: stringTags
        }),
      });

      if (response.ok) {
        // Success! Trigger the green checkmark UI and disable the button
        setSaveStatus('saved');
        // If your file has an setIsDirty function, uncomment the next line:
        // setIsDirty(false); 
        
        // Reset the button back to the standard state after 2 seconds
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        console.error("Backend refused the settings. Status:", response.status);
        setSaveStatus('error');
      }
    } catch (error) {
      console.error("Network or CORS Error:", error);
      setSaveStatus('error');
    }
  }

  // ── Render ──
  return (
    <div className="relative min-h-dvh grid-bg">
      <div className="pointer-events-none absolute inset-0 radial-depth" />

      {/* ── Header ── */}
      <header
        className="relative z-20 flex items-center justify-between px-6 py-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.055)' }}
      >
        {/* Wordmark */}
        <div className="flex items-center gap-3">
          <span
            className="text-[22px] font-black tracking-tighter leading-none"
            style={{
              fontFamily: 'var(--font-space-grotesk)',
              background: 'linear-gradient(145deg, #ffffff 15%, #4D4DFF 80%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            PULSE
          </span>
          <span
            className="rounded px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.2em]"
            style={{
              fontFamily: 'var(--font-space-grotesk)',
              background: 'rgba(77,77,255,0.1)',
              border: '1px solid rgba(77,77,255,0.28)',
              color: '#818cff',
            }}
          >
            Command Center
          </span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            <span
              className="text-[12px] text-white/38"
              style={{ fontFamily: 'var(--font-space-grotesk)' }}
            >
              Engine Active
            </span>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('pulse_token')
              window.location.href = '/'
            }}
            className="flex items-center gap-1.5 text-[12px] text-white/28 transition-colors hover:text-white/55"
            style={{ fontFamily: 'var(--font-space-grotesk)' }}
          >
            <LogOut size={13} />
            Exit
          </button>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="relative z-10 mx-auto max-w-3xl px-6 py-12">

        {/* Page heading */}
        <div className="animate-entrance mb-10">
          <h2
            className="text-[22px] font-bold text-white"
            style={{ fontFamily: 'var(--font-space-grotesk)' }}
          >
            Neural Configuration
          </h2>
          <p
            className="mt-1 text-[13px]"
            style={{ fontFamily: 'var(--font-inter)', color: 'rgba(255,255,255,0.32)' }}
          >
            Configure your AI brain&rsquo;s credentials and cognitive focus areas.
          </p>
        </div>

        {loading ? (
          /* Loading skeleton */
          <div className="space-y-5">
            {[1, 2].map((n) => (
              <div
                key={n}
                className="h-56 animate-pulse rounded-2xl"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-5">

            {/* ── Card 1: The Vault ── */}
            <GlassCard
              accentColor="indigo"
              className="animate-entrance"
            >
              <CardHeader
                icon={Key}
                title="The Vault"
                subtitle="API credentials are stored encrypted at rest. Never logged."
                accentColor="indigo"
              />

              <div className="space-y-4">
                <PasswordInput
                  id="groq-key"
                  label="Groq API Key"
                  placeholder="gsk_••••••••••••••••••••••••"
                  value={groqKey}
                  onChange={(v) => { setGroqKey(v); markDirty() }}
                  icon={Zap}
                />
                <PasswordInput
                  id="tavily-key"
                  label="Tavily API Key"
                  placeholder="tvly-••••••••••••••••••••••"
                  value={tavilyKey}
                  onChange={(v) => { setTavilyKey(v); markDirty() }}
                  icon={Key}
                />
              </div>
            </GlassCard>

            {/* ── Card 2: Neural Profile ── */}
            <GlassCard
              accentColor="coral"
              className="animate-entrance"
              // slight delay for stagger
            >
              <CardHeader
                icon={Brain}
                title="Neural Profile"
                subtitle="Define your cognitive focus — what PULSE monitors and digests for you."
                accentColor="coral"
              />

              <TagInput
                tags={tags}
                onAdd={handleAddTag}
                onRemove={handleRemoveTag}
              />

              {tags.length === 0 && (
                <p
                  className="mt-5 text-center text-[12px]"
                  style={{
                    fontFamily: 'var(--font-inter)',
                    color: 'rgba(255,255,255,0.2)',
                  }}
                >
                  No topics configured — add your first interest above.
                </p>
              )}
            </GlassCard>

            {/* ── Sync Button ── */}
            <div className="animate-entrance flex items-center justify-between pt-2">
              {/* Dirty hint */}
              <p
                className="text-[12px] transition-opacity duration-300"
                style={{
                  fontFamily: 'var(--font-inter)',
                  color: 'rgba(255,255,255,0.25)',
                  opacity: isDirty ? 1 : 0,
                }}
              >
                Unsaved changes
              </p>

              <button
                onClick={handleSave}
                disabled={!isDirty || saveStatus === 'saving'}
                className={`flex items-center gap-2 rounded-xl px-8 py-3.5 text-[12px] font-bold uppercase tracking-[0.13em] transition-all duration-300 active:scale-[0.97] disabled:cursor-not-allowed ${
                  isDirty && saveStatus === 'idle' ? 'sync-glow' : ''
                }`}
                style={{
                  fontFamily: 'var(--font-space-grotesk)',
                  background:
                    saveStatus === 'saved'
                      ? 'linear-gradient(135deg, #22c55e, #16a34a)'
                      : saveStatus === 'error'
                      ? 'linear-gradient(135deg, #ef4444, #b91c1c)'
                      : isDirty
                      ? 'linear-gradient(135deg, #4D4DFF 0%, #6e6eff 100%)'
                      : 'rgba(255,255,255,0.05)',
                  border: isDirty ? 'none' : '1px solid rgba(255,255,255,0.09)',
                  color: isDirty || saveStatus !== 'idle' ? '#fff' : 'rgba(255,255,255,0.3)',
                  opacity: !isDirty && saveStatus === 'idle' ? 0.6 : 1,
                }}
              >
                {saveStatus === 'saving' ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/25 border-t-white" />
                    Syncing…
                  </>
                ) : saveStatus === 'saved' ? (
                  <>
                    <CheckCircle2 size={14} />
                    Profile Synced
                  </>
                ) : saveStatus === 'error' ? (
                  <>
                    <AlertCircle size={14} />
                    Sync Failed
                  </>
                ) : (
                  <>
                    <Save size={14} />
                    Sync Profile
                  </>
                )}
              </button>
            </div>

          </div>
        )}
      </main>
    </div>
  )
}
