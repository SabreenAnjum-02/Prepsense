import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'
import { BrainCircuit, Activity, ArrowUpRight } from 'lucide-react'

export const metadata: Metadata = {
  title: 'PrepSense Enterprise | Autonomous AI Assessment & Video Evaluation',
  description: 'Role-grounded adaptive technical video interviewing, isolated subprocess coding sandbox, and deterministic 6D competency intelligence.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-800 min-h-screen flex flex-col selection:bg-blue-500/20 selection:text-blue-900">
        
        {/* Navigation Bar */}
        <header className="border-b border-slate-200 bg-white/80 backdrop-blur-xl sticky top-0 z-50 transition-all">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3.5 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 via-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 group-hover:shadow-blue-500/30 transition-all">
                  <BrainCircuit className="w-5 h-5 text-white stroke-[2.5]" />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
              </div>
              
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-black tracking-tight text-slate-900 group-hover:text-blue-600 transition-colors">
                    PREPSENSE
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 font-medium tracking-wide">Enterprise Assessment Engine</p>
              </div>
            </Link>

            <nav className="flex items-center gap-4 sm:gap-6 text-xs font-semibold text-slate-600">
              <Link href="/" className="hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1">
                <span>Overview</span>
              </Link>
              <Link href="/intake" className="hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1">
                <span>Assessments</span>
              </Link>
              
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-[11px] text-slate-600">
                <Activity className="w-3 h-3 text-blue-500" />
                <span className="font-mono text-blue-600">6D Core</span>
                <span className="text-slate-300">&bull;</span>
                <span className="text-slate-500">Secure Sandbox</span>
              </div>

              <Link
                href="/intake"
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all shadow-md shadow-blue-600/20 hover:shadow-blue-600/30 flex items-center gap-1.5"
              >
                <span>Launch Session</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 bg-white/60 py-8 relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span>PrepSense Intelligence &bull; Production Architecture v2.0</span>
            </div>
            <div className="flex items-center gap-4 text-slate-500">
              <a href="/api/docs" target="_blank" rel="noreferrer" className="hover:text-blue-600 transition-colors flex items-center gap-1">
                <span>OpenAPI Specs</span>
              </a>
              <span>&bull;</span>
              <span>All 9 Archetypes Supported</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
