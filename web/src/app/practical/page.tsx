'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api, PracticalTask, PracticalSubmitResult } from '@/lib/api'
import {
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  ArrowRight,
  Code2,
  FileText,
  ShieldCheck,
  Terminal,
  Clock,
  Cpu,
  Sparkles,
  Layers
} from 'lucide-react'

function PracticalContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id') || (typeof window !== 'undefined' ? localStorage.getItem('prepsense_session_id') : '')

  const [task, setTask] = useState<PracticalTask | null>(null)
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<PracticalSubmitResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'tests' | 'stdout'>('tests')

  useEffect(() => {
    if (!sessionId) {
      router.push('/intake')
      return
    }

    const loadTask = async () => {
      try {
        const taskData = await api.getPracticalTask(sessionId)
        setTask(taskData)
        setCode(taskData.starter_code || '')
      } catch (err: any) {
        setError(err.message || 'Failed to load practical task.')
      } finally {
        setLoading(false)
      }
    }
    loadTask()
  }, [sessionId, router])

  const handleRunAndSubmit = async () => {
    if (!code.trim() || !sessionId || !task) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await api.submitPractical(sessionId, code, task.language)
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Execution error in sandbox.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleViewReport = () => {
    router.push(`/report?session_id=${sessionId}`)
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
        <p className="text-sm text-slate-400 font-mono">Loading role practical assessment workspace...</p>
      </div>
    )
  }

  const isCodingRole = task?.task_type === 'CODING' || task?.task_type === 'INFRA_SCRIPT' || task?.task_type === 'DATA_ANALYSIS'

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fadeIn pb-8">
      {/* Top IDE Header Bar */}
      <div className="p-4 sm:p-5 rounded-3xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-2xl backdrop-blur">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {isCodingRole ? <Code2 className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-white">{task?.title}</h1>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-emerald-400">
                {task?.task_type}
              </span>
            </div>
            <p className="text-xs text-slate-400">Role: <span className="text-slate-200">{task?.role_archetype}</span> &bull; Engine: <span className="text-slate-300 font-mono">{task?.language}</span></p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-400">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span>Time Limit: {task?.time_limit_minutes || 15} min</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-950/70 border border-emerald-800/60 text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
            <span>Isolated Sandbox</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-[11px] underline">Dismiss</button>
        </div>
      )}

      {/* Split-Pane Studio Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Pane: Task Spec & Test Cases */}
        <div className="lg:col-span-5 space-y-4 flex flex-col">
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-xl flex-1 overflow-y-auto max-h-[600px]">
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>Specification & Constraints</span>
            </div>

            <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 font-sans">
              {task?.description}
            </div>

            {task?.visible_test_cases && task.visible_test_cases.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Visible Example Test Cases</h4>
                <div className="space-y-2">
                  {task.visible_test_cases.map((tc, idx) => (
                    <div key={idx} className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>Test #{idx + 1}: {tc.description || `Example ${idx + 1}`}</span>
                      </div>
                      <div className="text-slate-300 bg-slate-900/80 p-2 rounded-xl border border-slate-800/60 text-[11px] break-all">
                        <span className="text-slate-500 mr-2">Input:</span>{typeof tc.input_params === 'object' ? JSON.stringify(tc.input_params) : String(tc.input_params)}
                      </div>
                      <div className="text-emerald-400 bg-slate-900/80 p-2 rounded-xl border border-slate-800/60 text-[11px] break-all">
                        <span className="text-slate-500 mr-2">Expected:</span>{typeof tc.expected_output === 'object' ? JSON.stringify(tc.expected_output) : String(tc.expected_output)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: Code Editor & Terminal Results */}
        <div className="lg:col-span-7 space-y-4 flex flex-col">
          <div className="rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl overflow-hidden flex-1 flex flex-col">
            {/* Editor Tab Bar */}
            <div className="px-4 py-2.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono font-bold text-slate-200 flex items-center gap-2">
                  <Code2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{isCodingRole ? (task?.language === 'python' ? 'solution.py' : 'solution.js') : 'solution.md'}</span>
                </div>
              </div>

              <div className="text-[11px] font-mono text-slate-500">
                UTF-8 &bull; {task?.language}
              </div>
            </div>

            {/* Code Input Area */}
            <div className="p-4 flex-1 bg-[#090d16]">
              <textarea
                rows={16}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Write your implementation here..."
                className="w-full h-full min-h-[340px] bg-transparent text-emerald-300 font-mono text-xs sm:text-sm leading-relaxed p-2 focus:outline-none resize-none"
                spellCheck={false}
              />
            </div>

            {/* Action Bar */}
            <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Submissions are evaluated against visible & unforgeable hidden edge-cases.
              </span>

              <button
                type="button"
                onClick={handleRunAndSubmit}
                disabled={submitting || !code.trim()}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-40"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Executing in Subprocess Sandbox...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run & Evaluate Solution</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Terminal / Test Case Results Card */}
          {result && (
            <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-bold text-white">Execution & Sandbox Output</h3>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-extrabold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                    Practical Score: {result.overall_practical_score}/100
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono">Tests Passed</span>
                  <div className="font-bold text-emerald-400 text-sm mt-0.5">
                    {result.tests_passed}/{result.total_tests}
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono">Hidden Passed</span>
                  <div className="font-bold text-teal-400 text-sm mt-0.5">
                    {result.hidden_tests_passed}/{result.total_hidden_tests}
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono">Complexity</span>
                  <div className="font-bold text-slate-200 text-sm mt-0.5">
                    {result.time_complexity} Time
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono">Code Quality</span>
                  <div className="font-bold text-cyan-400 text-sm mt-0.5">
                    {result.code_quality_score}/100
                  </div>
                </div>
              </div>

              {result.feedback && (
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                  {result.feedback}
                </div>
              )}

              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleViewReport}
                  className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all group"
                >
                  <span>Generate Final 6D Dossier</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function PracticalPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading IDE...</p>
      </div>
    }>
      <PracticalContent />
    </Suspense>
  )
}
