'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { X, Hash } from 'lucide-react'

export interface Tag {
  id: string
  label: string
}

interface TagInputProps {
  tags: Tag[]
  onAdd: (label: string) => void
  onRemove: (id: string) => void
  maxTags?: number
}

export default function TagInput({
  tags,
  onAdd,
  onRemove,
  maxTags = 20,
}: TagInputProps) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  function commit() {
    const trimmed = value.trim()
    if (!trimmed) return
    if (tags.length >= maxTags) return
    // Avoid exact duplicates (case-insensitive)
    if (tags.some((t) => t.label.toLowerCase() === trimmed.toLowerCase())) {
      setValue('')
      return
    }
    onAdd(trimmed)
    setValue('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      commit()
    }
    // Backspace on empty input removes the last tag
    if (e.key === 'Backspace' && value === '' && tags.length > 0) {
      onRemove(tags[tags.length - 1].id)
    }
  }

  const reachedMax = tags.length >= maxTags

  return (
    <div className="space-y-3">
      {/* Text input */}
      <div
        className="pulse-input flex items-center gap-3 rounded-lg px-4 py-3.5 transition-all duration-250"
        style={{
          background: 'rgba(255,255,255,0.028)',
          border: '1px solid rgba(255,255,255,0.08)',
          cursor: 'text',
        }}
        onClick={() => inputRef.current?.focus()}
      >
        <Hash size={14} style={{ color: 'rgba(255,107,107,0.5)', flexShrink: 0 }} />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={reachedMax ? `Max ${maxTags} topics reached` : 'Add a topic… (press Enter)'}
          disabled={reachedMax}
          maxLength={48}
          className="flex-1 bg-transparent text-[13px] text-white placeholder-white/20 focus:outline-none disabled:cursor-not-allowed"
          style={{ fontFamily: 'var(--font-inter)' }}
        />
        {value.trim() && (
          <kbd
            className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
            style={{
              fontFamily: 'var(--font-space-grotesk)',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(255,255,255,0.3)',
            }}
          >
            ↵
          </kbd>
        )}
      </div>

      {/* Tag pills */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag.id}
              className="tag-appear inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold transition-all duration-150 hover:brightness-110"
              style={{
                fontFamily: 'var(--font-space-grotesk)',
                background: 'rgba(255,107,107,0.1)',
                border: '1px solid rgba(255,107,107,0.32)',
                color: '#ff8f8f',
                boxShadow: '0 0 12px rgba(255,107,107,0.18)',
              }}
            >
              {tag.label}
              <button
                type="button"
                onClick={() => onRemove(tag.id)}
                aria-label={`Remove ${tag.label}`}
                className="flex items-center justify-center rounded-full p-0.5 transition-colors duration-100 hover:bg-[#FF6B6B]/20"
                style={{ color: 'rgba(255,143,143,0.65)' }}
              >
                <X size={10} strokeWidth={2.5} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Helper */}
      <p
        className="text-[11px]"
        style={{
          fontFamily: 'var(--font-inter)',
          color: 'rgba(255,255,255,0.18)',
        }}
      >
        {tags.length}/{maxTags} topics · Backspace removes last
      </p>
    </div>
  )
}
