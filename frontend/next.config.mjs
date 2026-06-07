/** @type {import('next').NextConfig} */
const nextConfig = {
  // Point to your FastAPI backend. Override via NEXT_PUBLIC_API_URL env var.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

export default nextConfig
