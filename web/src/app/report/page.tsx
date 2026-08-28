'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api, FinalReport } from '@/lib/api'
import {
  CheckCircle2,
  AlertCircle,
  Award,
  ArrowLeft,
  Printer,
  Sparkles,
  Layers,
  Cpu,
  MessageSquare,
  Users,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Briefcase
} from 'lucide-react'

function ReportContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id') || (typeof window !== 'undefined' ? localStorage.getItem('prepsense_session_id') : '')

  const [report, setReport] = useState<FinalReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      router.push('/intake')
      return
    }

    const loadReport = async () => {
      try {
        const data = await api.getFinalReport(sessionId)
        setReport(data)
      } catch (err: any) {
        setError(err.message || 'Failed to generate report.')
      } finally {
        setLoading(false)
      }
    }
    loadReport()
  }, [sessionId, router])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-emerald-400 animate-spin" />
        </div>
        <div className="text-center space-y-1">
          <h3 className="text-lg font-bold text-white">Synthesizing 6-Dimensional Evidence Report</h3>
          <p className="text-xs text-slate-400">Evaluating technical depth, practical execution, and role alignment...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="max-w-xl mx-auto p-6 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Report Generation Error</h2>
        <p className="text-xs text-slate-400">{error || 'Session report not available.'}</p>
        <button
          onClick={() => router.push('/intake')}
          className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
        >
          Start New Assessment
        </button>
      </div>
    )
  }

  const dims = [
    { label: 'Technical Depth & Architecture', val: report.dimension_scores.technical, icon: Cpu, weight: '35%' },
    { label: 'Practical Sandbox Execution', val: report.dimension_scores.practical, icon: Layers, weight: '20%' },
    { label: 'Problem Solving & Trade-offs', val: report.dimension_scores.problem_solving, icon: Sparkles, weight: '20%' },
    { label: 'Communication & STAR Structure', val: report.dimension_scores.communication, icon: MessageSquare, weight: '10%' },
    { label: 'Behavioral & Incident Leadership', val: report.dimension_scores.behavioral, icon: Users, weight: '10%' },
    { label: 'Role Competency & Culture Fit', val: report.dimension_scores.role_fit, icon: Award, weight: '5%' },
  ]

  const isHire = report.hiring_recommendation.toLowerCase().includes('hire')

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-4">
      {/* Top Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Comprehensive Evaluation Complete</span>
            <span>&bull;</span>
            <span>{report.confidence_level} Confidence</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">{report.candidate_name}</h1>
          <p className="text-sm text-slate-400 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-emerald-400" />
            <span>Target Role: <strong className="text-slate-200">{report.target_role}</strong></span>
          </p>
        </div>

        <div className="flex items-center gap-5">
          <div className="text-right">
            <div className="text-4xl sm:text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300">
              {report.final_score.toFixed(1)}
            </div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Overall Score / 100</div>
          </div>

          <div className={`px-5 py-3 rounded-2xl text-xs font-extrabold uppercase tracking-wider border shadow-lg ${
            isHire
              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-emerald-500/10'
              : 'bg-rose-500/15 text-rose-300 border-rose-500/30 shadow-rose-500/10'
          }`}>
            {report.hiring_recommendation}
          </div>
        </div>
      </div>

      {/* Qualitative Performance Summary */}
      <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <span>Executive Assessment Summary</span>
        </h3>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">{report.overall_summary}</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-emerald-400">Technical Depth Assessment</span>
            <p className="text-xs text-slate-400 leading-relaxed">{report.technical_assessment}</p>
          </div>
          <div className="space-y-1">
            <span className="text-xs font-semibold text-teal-400">Communication & Articulation</span>
            <p className="text-xs text-slate-400 leading-relaxed">{report.communication_assessment}</p>
          </div>
        </div>
      </div>

      {/* 6-Dimensional Evidence Scorecard */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-200">6-Dimensional Evidence Breakdown</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {dims.map((d, idx) => {
            const Icon = d.icon
            return (
              <div key={idx} className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-md">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-slate-300 font-semibold">
                    <Icon className="w-4 h-4 text-emerald-400" />
                    <span>{d.label}</span>
                  </div>
                  <span className="font-extrabold text-white text-sm">{d.val.toFixed(1)}</span>
                </div>
                <div className="w-full bg-slate-950 h-2.5 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(100, Math.max(0, d.val))}%` }}
                  />
                </div>
                <div className="text-[10px] text-slate-500 font-medium">Stage Weight: {d.weight}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Practical Assessment Section */}
      {report.practical_evaluation && (
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Practical Sandbox & Code Execution</h3>
            </div>
            <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              Score: {report.practical_evaluation.overall_practical_score}/100
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-400 text-[11px]">Task Evaluated</span>
              <div className="font-semibold text-slate-200 mt-1">{report.practical_evaluation.task_title}</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-400 text-[11px]">Test Suite Results</span>
              <div className="font-semibold text-emerald-400 mt-1">
                {report.practical_evaluation.tests_passed}/{report.practical_evaluation.total_tests} Passed (Hidden: {report.practical_evaluation.hidden_tests_passed}/{report.practical_evaluation.total_hidden_tests})
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-400 text-[11px]">Complexity Verified</span>
              <div className="font-semibold text-teal-400 mt-1">{report.practical_evaluation.time_complexity} Time</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-400 text-[11px]">Code Quality</span>
              <div className="font-semibold text-slate-200 mt-1">{report.practical_evaluation.code_quality_score}/100</div>
            </div>
          </div>

          {report.practical_evaluation.feedback && (
            <p className="text-xs text-slate-300 italic p-3 rounded-xl bg-slate-950 border border-slate-800">
              &ldquo;{report.practical_evaluation.feedback}&rdquo;
            </p>
          )}
        </div>
      )}

      {/* Strengths & Targeted Skill Roadmap */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            <span>Demonstrated Strengths</span>
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {report.strengths.map((s, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-teal-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span>Targeted Growth & Improvement Roadmap</span>
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {report.improvement_plan.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="w-4 h-4 rounded-full bg-teal-500/10 text-teal-400 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5 border border-teal-500/20">
                  {idx + 1}
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-4">
        <button
          type="button"
          onClick={() => router.push('/intake')}
          className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Start New Assessment</span>
        </button>

        <button
          type="button"
          onClick={() => window.print()}
          className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all"
        >
          <Printer className="w-4 h-4" />
          <span>Export Official PDF Report</span>
        </button>
      </div>
    </div>
  )
}

export default function ReportPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Sparkles className="w-8 h-8 text-emerald-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading final report...</p>
      </div>
    }>
      <ReportContent />
    </Suspense>
  )
}
