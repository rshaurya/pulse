'use client'

import { useState, type ElementType } from 'react'
import { Eye, EyeOff } from 'lucide-react'

interface PasswordInputProps {
  id: string
  label: string
  placeholder: string
  value: string
  onChange: (value: string) => void
  /** Lucide icon component shown in the label */
  icon: ElementType
  disabled?: boolean
}

export default function PasswordInput({
  id,
  label,
  placeholder,
  value,
  onChange,
  icon: Icon,
  disabled = false,
}: PasswordInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="space-y-2">
      {/* Label */}
      <label
        htmlFor={id}
        className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.15em]"
        style={{
          fontFamily: 'var(--font-space-grotesk)',
          color: 'rgba(255,255,255,0.38)',
        }}
      >
        <Icon size={11} style={{ color: '#6e6eff' }} />
        {label}
      </label>

      {/* Input wrapper */}
      <div
        className="pulse-input flex items-center gap-3 rounded-lg px-4 py-3.5 transition-all duration-250"
        style={{
          background: 'rgba(255,255,255,0.028)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
          className="flex-1 bg-transparent text-[13px] text-white placeholder-white/18 focus:outline-none disabled:cursor-not-allowed font-mono tracking-wider"
          style={{ fontFamily: 'var(--font-inter)' }}
        />

        {/* Eye toggle */}
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide key' : 'Show key'}
          className="shrink-0 rounded p-0.5 transition-colors duration-150 hover:text-white/60"
          style={{ color: 'rgba(255,255,255,0.25)' }}
        >
          {visible ? <EyeOff size={15} /> : <Eye size={15} />}
        </button>
      </div>
    </div>
  )
}
