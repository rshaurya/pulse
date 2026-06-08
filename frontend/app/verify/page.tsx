'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Loader2 } from 'lucide-react'

function VerifyLogic() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState('Authenticating connection...')

  useEffect(() => {
    if (!token) {
      setStatus('No token detected. Access denied.')
      return
    }

    const verifyToken = async () => {
      try {
        // The API Call to validate the token with FastAPI
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`{API_URL}/api/auth/verify?token=${token}`)
        
        if (response.ok) {
          const data = await response.json()
          
          // Securely save the user_id in the browser's Local Storage
          localStorage.setItem('pulse_user_id', data.user_id.toString())
          
          setStatus('Authentication successful. Rerouting to Neural Profile...')
          
          // Teleport the user to the dashboard after a brief delay
          setTimeout(() => {
            router.push('/dashboard')
          }, 800)
        } else {
          setStatus('Token expired or invalid. Please request a new link.')
        }
      } catch (error) {
        console.error("Verification Error:", error)
        setStatus('Network error. Backend unreachable.')
      }
    }

    verifyToken()
  }, [token, router])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0B0F19] text-white">
      <Loader2 className="mb-4 h-8 w-8 animate-spin text-[#4D4DFF]" />
      <p className="font-mono text-sm text-slate-400" style={{ fontFamily: 'var(--font-space-grotesk)' }}>
        {status}
      </p>
    </div>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[#0B0F19]">
        <Loader2 className="h-8 w-8 animate-spin text-[#4D4DFF]" />
      </div>
    }>
      <VerifyLogic />
    </Suspense>
  )
}