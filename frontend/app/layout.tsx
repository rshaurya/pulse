import type { Metadata } from 'next'
import { Space_Grotesk, Inter } from 'next/font/google'
// Ignore missing type declarations for CSS side-effect import
// @ts-ignore: Cannot find module or type declarations for CSS
import './globals.css'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'PULSE — AI Knowledge Engine',
  description:
    'Your self-hosted, personalized AI news & knowledge digest. Headless. Autonomous. Always on.',
  themeColor: '#0B0F19',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable}`}
      suppressHydrationWarning
    >
      <body className="bg-[#0B0F19] text-white min-h-dvh antialiased">
        {children}
      </body>
    </html>
  )
}
