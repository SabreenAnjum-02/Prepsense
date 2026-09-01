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
    <html lang="en" className="dark">
      <body className="bg-[#070b12] text-slate-100 min-h-screen flex flex-col selection:bg-emerald-500/30 selection:text-emerald-200">
        {/* Top Intelligence Grid Background */}
        <div className="fixed inset-0 bg-grid-pattern pointer-events-none opacity-40 z-0" />
        
        {/* Navigation Bar */}
        <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50 transition-all">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3.5 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 group-hover:shadow-emerald-500/30 transition-all">
                  <BrainCircuit className="w-5 h-5 text-slate-950 stroke-[2.5]" />
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950 animate-pulse" />
              </div>
              
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-black tracking-tight text-white group-hover:text-emerald-300 transition-colors">
                    PREPSENSE
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 font-medium tracking-wide">Autonomous Assessment Engine</p>
              </div>
            </Link>

            <nav className="flex items-center gap-4 sm:gap-6 text-xs font-semibold text-slate-400">
              <Link href="/" className="hover:text-white transition-colors flex items-center gap-1.5 py-1">
                <span>Overview</span>
              </Link>
              <Link href="/intake" className="hover:text-emerald-400 transition-colors flex items-center gap-1.5 py-1">
                <span>Assessments</span>
              </Link>
              
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-[11px] text-slate-300">
                <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
                <span className="font-mono text-emerald-400">Deterministic 6D Engine</span>
                <span className="text-slate-600">&bull;</span>
                <span className="text-slate-400">Subprocess Sandbox</span>
              </div>

              <Link
                href="/intake"
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-all shadow-md shadow-emerald-600/20 hover:shadow-emerald-600/30 flex items-center gap-1.5"
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
        <footer className="border-t border-slate-800/80 bg-slate-950/60 py-8 relative z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>PrepSense Intelligence &bull; Production Architecture v2.0</span>
            </div>
            <div className="flex items-center gap-4 text-slate-400">
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-emerald-400 transition-colors flex items-center gap-1">
                <span>FastAPI OpenAPI Specs</span>
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
