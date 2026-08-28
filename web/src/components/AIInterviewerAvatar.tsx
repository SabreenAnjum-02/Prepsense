'use client'

import React from 'react'
import { Mic, Volume2, BrainCircuit, Activity } from 'lucide-react'

export type InterviewerState = 'IDLE' | 'SPEAKING' | 'LISTENING' | 'THINKING'

interface AIInterviewerAvatarProps {
  state: InterviewerState
  interviewerName?: string
  roleTitle?: string
}

export function AIInterviewerAvatar({
  state,
  interviewerName = 'Alex',
  roleTitle = 'Lead AI Interviewer'
}: AIInterviewerAvatarProps) {
  return (
    <div className="relative w-full aspect-video sm:aspect-[16/10] rounded-3xl overflow-hidden bg-slate-900 border border-slate-800/60 shadow-2xl flex flex-col p-6 group transition-all duration-500">
      
      {state === 'SPEAKING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent pointer-events-none animate-pulse" />
      )}
      {state === 'LISTENING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-emerald-500/10 via-transparent to-transparent pointer-events-none" />
      )}
      {state === 'THINKING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-500/10 via-transparent to-transparent pointer-events-none" />
      )}

      {/* Top Bar Status Indicator */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-950/50 backdrop-blur-md border border-slate-700/50 shadow-sm">
          <div className={`w-2 h-2 rounded-full ${state === 'IDLE' ? 'bg-slate-500' : 'bg-emerald-400 animate-pulse'}`} />
          <span className="text-xs font-semibold text-slate-200 tracking-wide">{interviewerName}</span>
          <span className="text-slate-600">&bull;</span>
          <span className="text-[11px] text-slate-400 font-medium">{roleTitle}</span>
        </div>
      </div>

      {/* Center Persona Visualization */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center space-y-6">
        <div className="relative">
          {/* Outer Aura */}
          <div
            className={`w-32 h-32 sm:w-44 sm:h-44 rounded-full flex items-center justify-center transition-all duration-700 ${
              state === 'SPEAKING'
                ? 'bg-blue-500/10 ring-4 ring-blue-500/20 scale-105'
                : state === 'LISTENING'
                ? 'bg-emerald-500/10 ring-4 ring-emerald-500/20 scale-100'
                : state === 'THINKING'
                ? 'bg-purple-500/10 ring-4 ring-purple-500/20 animate-pulse'
                : 'bg-slate-800/30 ring-2 ring-slate-800/50'
            }`}
          >
            {/* Core Humanoid / Neural Node */}
            <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full bg-gradient-to-tr from-slate-900 via-slate-800 to-slate-900 border border-slate-700/50 flex items-center justify-center shadow-inner relative overflow-hidden">
              {state === 'SPEAKING' && (
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-6 bg-blue-400 rounded-full animate-[bounce_1s_infinite_0ms]" />
                  <div className="w-1.5 h-10 bg-blue-400 rounded-full animate-[bounce_1s_infinite_200ms]" />
                  <div className="w-1.5 h-8 bg-blue-400 rounded-full animate-[bounce_1s_infinite_400ms]" />
                  <div className="w-1.5 h-12 bg-blue-400 rounded-full animate-[bounce_1s_infinite_100ms]" />
                  <div className="w-1.5 h-7 bg-blue-400 rounded-full animate-[bounce_1s_infinite_300ms]" />
                </div>
              )}

              {state === 'LISTENING' && (
                <div className="relative flex items-center justify-center">
                  <Mic className="w-10 h-10 text-emerald-400 opacity-90" />
                </div>
              )}

              {state === 'THINKING' && (
                <BrainCircuit className="w-12 h-12 text-purple-400 animate-pulse opacity-90" />
              )}

              {state === 'IDLE' && (
                <div className="w-3 h-3 rounded-full bg-slate-500 animate-pulse" />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
