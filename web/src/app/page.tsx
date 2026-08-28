'use client'

import Link from 'next/link'
import {
  ArrowRight,
  Code2,
  Cpu,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Terminal,
  FileText,
  Layers,
  Activity,
  Zap,
  Lock,
  Compass,
  Database,
  BarChart3,
  Bot,
  Video,
  Mic,
  ArrowUpRight
} from 'lucide-react'

export default function LandingPage() {
  const roles = [
    { title: 'Backend Software Engineer', tag: 'Python / Java / Go', desc: 'Distributed microservices, concurrency, caching, and LRU algorithms.', icon: Cpu, color: 'from-emerald-500/20 to-teal-500/10' },
    { title: 'Frontend Engineer', tag: 'React / Next.js / TypeScript', desc: 'Event loops, React reconciliation, DOM performance, and state systems.', icon: Code2, color: 'from-cyan-500/20 to-blue-500/10' },
    { title: 'Full Stack Engineer', tag: 'TypeScript / Node / SQL', desc: 'End-to-end fullstack architecture, query parsing, and API layers.', icon: Layers, color: 'from-indigo-500/20 to-purple-500/10' },
    { title: 'Data Scientist / ML Engineer', tag: 'PyTorch / Metrics / Scikit', desc: 'Binary classification metrics, loss functions, and drift monitoring.', icon: BarChart3, color: 'from-emerald-500/20 to-cyan-500/10' },
    { title: 'DevOps & Cloud Platform', tag: 'Kubernetes / Terraform / SRE', desc: 'IaC reliability, multi-AZ high availability, and anomaly triage.', icon: Terminal, color: 'from-teal-500/20 to-emerald-500/10' },
    { title: 'Cybersecurity & AppSec', tag: 'OWASP / Injection / Auth', desc: 'Threat payload defense, zero-trust protocols, and vulnerability analysis.', icon: Lock, color: 'from-rose-500/20 to-orange-500/10' },
    { title: 'Mobile Engineer', tag: 'React Native / Swift / Kotlin', desc: 'Offline-first sync, conflict resolvers, and client persistence.', icon: Compass, color: 'from-blue-500/20 to-cyan-500/10' },
    { title: 'UI/UX Designer', tag: 'WCAG 2.1 / Design Systems', desc: 'Accessibility compliance, component hierarchies, and UX teardowns.', icon: Sparkles, color: 'from-fuchsia-500/20 to-pink-500/10' },
    { title: 'Technical Product Manager', tag: 'RICE / PRD / North Star', desc: '0-to-1 MVP feature prioritization, telemetry, and trade-off matrices.', icon: FileText, color: 'from-amber-500/20 to-yellow-500/10' },
  ]

  const workflowStages = [
    { num: '01', title: 'Candidate Intake & Role Grounding', desc: 'Resume parsing extracts skills, projects, and experience while matching against target role blueprint.' },
    { num: '02', title: 'Adaptive AI Video Interview', desc: '10–14 conversational questions across 5 stages with hands-free turn-taking and dynamic follow-up probing.' },
    { num: '03', title: 'Subprocess Practical Sandbox', desc: 'Isolated code execution with runtime limits, visible test cases, and unforgeable hidden edge-case suites.' },
    { num: '04', title: 'Deterministic 6D Dossier', desc: 'Evidence-grounded hiring scores, verifiable transcript citations, and role-specific candidate roadmap.' },
  ]

  return (
    <div className="space-y-24 py-6 animate-fadeIn">
      {/* Hero Section */}
      <section className="text-center space-y-8 max-w-5xl mx-auto pt-8">
        <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs font-semibold text-slate-300 shadow-xl backdrop-blur">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>PrepSense v2 Enterprise Intelligence Platform</span>
          <span className="text-slate-600">&bull;</span>
          <span className="text-emerald-400 font-mono">9 Domain Blueprints Active</span>
        </div>

        <h1 className="text-5xl sm:text-7xl font-black tracking-tight text-white leading-[1.08]">
          The Intelligent Standard for <br className="hidden sm:inline" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            Autonomous Technical Assessments
          </span>
        </h1>

        <p className="text-base sm:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed font-normal">
          Evaluate engineering talent with resume-grounded AI video interviews, real-time speech turn-taking, isolated execution sandboxes, and mathematical 6-dimensional evidence scoring.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Link
            href="/intake"
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-sm flex items-center justify-center gap-3 shadow-xl shadow-emerald-600/25 transition-all group"
          >
            <span>Launch Candidate Assessment</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1.5 transition-transform" />
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="w-full sm:w-auto px-6 py-4 rounded-2xl bg-slate-900/90 hover:bg-slate-800/90 text-slate-300 font-bold text-sm border border-slate-800/80 transition-all flex items-center justify-center gap-2"
          >
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>FastAPI OpenAPI Explorer</span>
          </a>
        </div>
      </section>

      {/* Enterprise Metrics Command Bar */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-6xl mx-auto">
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-1 text-center">
          <div className="text-3xl font-black text-white font-mono">10–14 Qs</div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Adaptive Progression</div>
          <div className="text-[11px] text-emerald-400/80">5-Stage Competency Gate</div>
        </div>

        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-1 text-center">
          <div className="text-3xl font-black text-emerald-400 font-mono">&lt; 8.0s</div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sandbox Timeout Guard</div>
          <div className="text-[11px] text-teal-400/80">Subprocess Isolated</div>
        </div>

        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-1 text-center">
          <div className="text-3xl font-black text-cyan-400 font-mono">6D Matrix</div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Deterministic Scoring</div>
          <div className="text-[11px] text-cyan-400/80">Evidence Traceable</div>
        </div>

        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur space-y-1 text-center">
          <div className="text-3xl font-black text-teal-400 font-mono">100% Voice</div>
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Hands-Free Conversational</div>
          <div className="text-[11px] text-emerald-400/80">Continuous Turn-Taking</div>
        </div>
      </section>

      {/* 4-Stage Architectural Pipeline */}
      <section className="space-y-8 max-w-6xl mx-auto">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-widest">
            <Zap className="w-3.5 h-3.5" />
            <span>Autonomous Assessment Pipeline</span>
          </div>
          <h2 className="text-3xl font-extrabold text-white">How PrepSense Evaluates Candidates</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {workflowStages.map((st, idx) => (
            <div key={idx} className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 space-y-3 relative group transition-all">
              <div className="text-3xl font-black text-slate-800 group-hover:text-emerald-500/20 transition-colors font-mono">
                {st.num}
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">{st.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{st.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Role Archetypes Directory */}
      <section className="space-y-8 max-w-6xl mx-auto">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Role Archetype Directory</div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">9 Domain Competency Blueprints</h2>
          </div>
          <Link href="/intake" className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
            <span>Configure Assessment &rarr;</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {roles.map((r, idx) => {
            const Icon = r.icon
            return (
              <div
                key={idx}
                className="p-6 rounded-3xl bg-slate-900/50 border border-slate-800/80 hover:border-emerald-500/30 transition-all flex flex-col justify-between space-y-4 group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-slate-800 text-emerald-400 border border-slate-700/60 group-hover:scale-105 transition-transform">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-mono text-slate-400 px-2.5 py-1 rounded-full bg-slate-950 border border-slate-800">
                      {r.tag}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-100 text-sm group-hover:text-emerald-300 transition-colors">{r.title}</h3>
                    <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{r.desc}</p>
                  </div>
                </div>

                <Link
                  href="/intake"
                  className="text-xs font-bold text-slate-400 group-hover:text-emerald-400 flex items-center gap-1.5 pt-2 border-t border-slate-800/60 transition-colors"
                >
                  <span>Select Role & Begin</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
