'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api, ResumeData, JDMatchResult } from '@/lib/api'
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Loader2,
  Sparkles,
  Briefcase,
  Layers,
  Cpu,
  Code2,
  Terminal,
  ShieldCheck,
  User,
  Mail,
  Zap
} from 'lucide-react'

export default function IntakePage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [candidateName, setCandidateName] = useState('')
  const [candidateEmail, setCandidateEmail] = useState('')
  const [targetRole, setTargetRole] = useState('Backend Software Engineer')
  const [skills, setSkills] = useState<string[]>([])
  const [experienceYears, setExperienceYears] = useState(3)
  const [jobDescription, setJobDescription] = useState('')
  
  const [parsing, setParsing] = useState(false)
  const [matching, setMatching] = useState(false)
  const [creating, setCreating] = useState(false)
  const [jdResult, setJdResult] = useState<JDMatchResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const roles = [
    { title: 'Backend Software Engineer', icon: Cpu, badge: 'Python / Distributed' },
    { title: 'Frontend Engineer', icon: Code2, badge: 'React / Next.js' },
    { title: 'Full Stack Engineer', icon: Layers, badge: 'TypeScript / Node' },
    { title: 'Data Scientist / ML Engineer', icon: Sparkles, badge: 'PyTorch / ML' },
    { title: 'DevOps & Cloud Platform Engineer', icon: Terminal, badge: 'Kubernetes / IaC' },
    { title: 'Cybersecurity & AppSec Engineer', icon: ShieldCheck, badge: 'OWASP / AppSec' },
    { title: 'Mobile Application Engineer', icon: Code2, badge: 'React Native / Swift' },
    { title: 'UI/UX Designer', icon: Sparkles, badge: 'Design System / a11y' },
    { title: 'Technical Product Manager', icon: Briefcase, badge: 'RICE / PRD' }
  ]

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return
    const uploadedFile = e.target.files[0]
    setFile(uploadedFile)
    setParsing(true)
    setError(null)

    try {
      const data: ResumeData = await api.uploadResume(uploadedFile, targetRole)
      setCandidateName(data.candidate_name)
      setCandidateEmail(data.candidate_email)
      setSkills(data.skills)
      setExperienceYears(data.experience_years || 3)
      if (data.detected_role) {
        setTargetRole(data.detected_role)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to parse resume.')
    } finally {
      setParsing(false)
    }
  }

  const handleMatchJD = async () => {
    if (!jobDescription.trim()) return
    setMatching(true)
    setError(null)
    try {
      const match = await api.matchJD(jobDescription, skills, targetRole)
      setJdResult(match)
      if (match.matched_role) {
        setTargetRole(match.matched_role)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to match job description.')
    } finally {
      setMatching(false)
    }
  }

  const handleStartAssessment = async () => {
    if (!candidateName.trim()) {
      setError('Please enter candidate name.')
      return
    }
    setCreating(true)
    setError(null)
    try {
      const session = await api.createSession({
        candidate_name: candidateName,
        candidate_email: candidateEmail || 'candidate@example.com',
        target_role: targetRole,
        skills: skills.length > 0 ? skills : ['Software Engineering', 'System Design'],
        experience_years: experienceYears,
        job_description: jobDescription
      })

      localStorage.setItem('prepsense_session_id', session.session_id)
      localStorage.setItem('prepsense_target_role', targetRole)
      localStorage.setItem('prepsense_candidate_name', candidateName)

      router.push(`/interview?session_id=${session.session_id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to initialize assessment session.')
      setCreating(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-4 animate-fadeIn">
      {/* Title Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/20">
          <Zap className="w-3.5 h-3.5" />
          <span>Candidate Intake & Blueprint Matching</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">Configure Assessment Session</h1>
        <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
          Upload a candidate resume or specify the target role to ground the adaptive interview question tree.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-[11px] underline hover:text-rose-300">Dismiss</button>
        </div>
      )}

      {/* Step 1: Target Role Selection Grid */}
      <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-mono">1</span>
            <span>Select Authoritative Target Role</span>
          </h2>
          <span className="text-xs text-slate-400">Controls 100% of the interview question domain</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {roles.map((r, idx) => {
            const Icon = r.icon
            const isSelected = targetRole === r.title
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setTargetRole(r.title)}
                className={`p-3.5 rounded-2xl border text-left flex items-start gap-3 transition-all ${
                  isSelected
                    ? 'bg-emerald-950/60 border-emerald-500 shadow-md shadow-emerald-500/10 ring-1 ring-emerald-500'
                    : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className={`p-2 rounded-xl shrink-0 ${isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="space-y-0.5">
                  <div className={`text-xs font-bold ${isSelected ? 'text-emerald-300' : 'text-slate-200'}`}>{r.title}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{r.badge}</div>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Step 2: Resume Intake & Profile */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-4 shadow-xl">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-xs font-mono">2</span>
            <span>Candidate Dossier & Resume</span>
          </h2>

          {/* Upload Dropzone */}
          <div className="relative border-2 border-dashed border-slate-700/80 hover:border-emerald-500/60 rounded-2xl p-6 text-center transition-all bg-slate-950/40">
            <input
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto">
                {parsing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
              </div>
              <div className="text-xs font-bold text-slate-200">
                {file ? file.name : 'Click or Drag & Drop Candidate Resume (PDF / TXT)'}
              </div>
              <p className="text-[11px] text-slate-500">Automatically extracts projects, skills, and seniority</p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div>
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Candidate Full Name</span>
              </label>
              <input
                type="text"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                placeholder="e.g. Alex Rivera"
                className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>Candidate Email</span>
              </label>
              <input
                type="email"
                value={candidateEmail}
                onChange={(e) => setCandidateEmail(e.target.value)}
                placeholder="alex.rivera@example.com"
                className="w-full mt-1 px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>

            {skills.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-400">Extracted Skills & Technologies:</span>
                <div className="flex flex-wrap gap-1.5">
                  {skills.map((s, idx) => (
                    <span key={idx} className="text-[11px] px-2.5 py-0.5 rounded-md bg-slate-800 text-emerald-300 border border-slate-700">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Step 3: Optional Job Description Matcher */}
        <div className="p-6 rounded-3xl bg-slate-900/70 border border-slate-800 space-y-4 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs font-mono">3</span>
                <span>Job Description Alignment (Optional)</span>
              </h2>
            </div>

            <textarea
              rows={5}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste job description requirements to tailor technical stage questions..."
              className="w-full p-3.5 rounded-2xl bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors resize-none leading-relaxed"
            />

            <button
              type="button"
              onClick={handleMatchJD}
              disabled={matching || !jobDescription.trim()}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-bold flex items-center justify-center gap-2 border border-slate-700 transition-colors disabled:opacity-40"
            >
              {matching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Analyze Job Description Alignment</span>
            </button>

            {jdResult && (
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2 text-xs animate-fadeIn">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Match Confidence:</span>
                  <span className="font-mono font-extrabold text-emerald-400">{jdResult.match_score}%</span>
                </div>
                <div className="space-y-1">
                  <span className="text-[11px] text-slate-400">Target Competencies:</span>
                  <div className="flex flex-wrap gap-1">
                    {jdResult.matched_competencies.map((m, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={handleStartAssessment}
              disabled={creating || !candidateName.trim()}
              className="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-extrabold text-sm flex items-center justify-center gap-2 shadow-xl shadow-emerald-600/25 transition-all disabled:opacity-40"
            >
              {creating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Initializing 5-Stage Adaptive Session...</span>
                </>
              ) : (
                <>
                  <span>Begin Autonomous Video Interview</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
