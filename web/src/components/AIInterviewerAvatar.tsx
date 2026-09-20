'use client'

import React from 'react'
import { BrainCircuit, Cpu } from 'lucide-react'

export type InterviewerState = 'IDLE' | 'SPEAKING' | 'LISTENING' | 'THINKING'

interface AIInterviewerAvatarProps {
  state: InterviewerState
  interviewerName?: string
  roleTitle?: string
}

export function AIInterviewerAvatar({
  state,
  interviewerName = 'N.E.X.U.S.',
  roleTitle = 'Technical AI Agent'
}: AIInterviewerAvatarProps) {
  return (
    <div className="relative w-full aspect-video sm:aspect-[16/10] rounded-3xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex flex-col p-6 group transition-all duration-500">
      
      {state === 'SPEAKING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-500/10 via-transparent to-transparent pointer-events-none animate-pulse" />
      )}
      {state === 'LISTENING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent pointer-events-none" />
      )}
      {state === 'THINKING' && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-500/10 via-transparent to-transparent pointer-events-none" />
      )}

      {/* Grid background pattern */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10 pointer-events-none" style={{ backgroundSize: '30px 30px' }} />

      {/* Top Bar Status Indicator */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700/50 shadow-sm">
          <Cpu className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-200 tracking-wider uppercase">{interviewerName}</span>
          <span className="text-slate-600">&bull;</span>
          <span className="text-[11px] text-slate-400 font-medium uppercase tracking-widest">{roleTitle}</span>
        </div>
      </div>

      {/* Center Persona Visualization - Futuristic Robot Core */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center space-y-6">
        <div className="relative flex items-center justify-center">
          
          {/* Outer Orbital Rings */}
          <div className={`absolute w-40 h-40 sm:w-56 sm:h-56 rounded-full border border-dashed transition-all duration-1000 ${
            state === 'THINKING' ? 'border-indigo-500/50 animate-[spin_4s_linear_infinite]' : 'border-slate-700 animate-[spin_20s_linear_infinite]'
          }`} />
          
          <div className={`absolute w-32 h-32 sm:w-44 sm:h-44 rounded-full border border-slate-600/50 transition-all duration-1000 ${
            state === 'SPEAKING' ? 'scale-110 border-cyan-500/50' : ''
          }`} />

          {/* Inner Core */}
          <div
            className={`relative w-24 h-24 sm:w-32 sm:h-32 rounded-full flex items-center justify-center backdrop-blur-md transition-all duration-700 ${
              state === 'SPEAKING'
                ? 'bg-cyan-950/80 ring-4 ring-cyan-500/50 shadow-[0_0_40px_rgba(6,182,212,0.4)] scale-110'
                : state === 'LISTENING'
                ? 'bg-blue-950/80 ring-2 ring-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.2)]'
                : state === 'THINKING'
                ? 'bg-indigo-950/80 ring-2 ring-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.3)]'
                : 'bg-slate-900/80 ring-1 ring-slate-700 shadow-inner'
            }`}
          >
            {/* Core icon / neural symbol */}
            <BrainCircuit className={`w-12 h-12 sm:w-16 sm:h-16 transition-all duration-500 ${
              state === 'SPEAKING' ? 'text-cyan-400 animate-pulse' :
              state === 'LISTENING' ? 'text-blue-400' :
              state === 'THINKING' ? 'text-indigo-400 animate-bounce' :
              'text-slate-500'
            }`} />

            {/* Speaking Audio Waveform (CSS simulated) */}
            {state === 'SPEAKING' && (
              <div className="absolute inset-0 flex items-center justify-center gap-1 opacity-70">
                {[...Array(5)].map((_, i) => (
                  <div 
                    key={i} 
                    className="w-1 bg-cyan-300 rounded-full animate-[pulse_1s_ease-in-out_infinite]"
                    style={{ 
                      height: `${20 + Math.random() * 40}%`,
                      animationDelay: `${i * 0.1}s` 
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* State Label */}
        <div className="flex flex-col items-center gap-1">
          <div className="px-4 py-1.5 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700">
            <span className={`text-xs font-bold tracking-widest uppercase ${
              state === 'SPEAKING' ? 'text-cyan-400' : 
              state === 'LISTENING' ? 'text-blue-400' : 
              state === 'THINKING' ? 'text-indigo-400' : 
              'text-slate-500'
            }`}>
              {state === 'IDLE' ? 'System Ready' : 
               state === 'SPEAKING' ? 'Transmitting' : 
               state === 'LISTENING' ? 'Receiving Input' : 
               'Processing'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
