'use client'

import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api, QuestionData } from '@/lib/api'
import { AIInterviewerAvatar, InterviewerState } from '@/components/AIInterviewerAvatar'
import { CandidateCamera } from '@/components/CandidateCamera'
import {
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Loader2,
  CheckCircle2,
  Video,
  ArrowRight,
  MonitorOff,
  ShieldCheck,
  BrainCircuit,
  Activity,
  Clock,
  CheckCircle,
  Circle,
  Play,
  Check
} from 'lucide-react'

// Simple Audio Queue for sequential playback of received chunks
class AudioPlayerQueue {
  private audioContext: AudioContext | null = null;
  private nextStartTime: number = 0;
  private sources: AudioBufferSourceNode[] = [];
  private isPlaying: boolean = false;

  init(ctx: AudioContext) {
    this.audioContext = ctx;
  }

  async addChunk(pcm16Data: ArrayBuffer) {
    if (!this.audioContext) return;
    
    // Convert PCM16 to Float32
    const int16 = new Int16Array(pcm16Data);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768.0;
    }

    const audioBuffer = this.audioContext.createBuffer(1, float32.length, 16000);
    audioBuffer.getChannelData(0).set(float32);

    const source = this.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext.destination);
    
    const currentTime = this.audioContext.currentTime;
    if (this.nextStartTime < currentTime) {
      this.nextStartTime = currentTime + 0.05; // 50ms buffer
    }

    source.start(this.nextStartTime);
    this.nextStartTime += audioBuffer.duration;
    this.sources.push(source);
    this.isPlaying = true;
  }

  stopAll() {
    this.sources.forEach(source => {
      try { source.stop(); } catch (e) {}
    });
    this.sources = [];
    this.nextStartTime = 0;
    if (this.audioContext) {
      this.nextStartTime = this.audioContext.currentTime;
    }
    this.isPlaying = false;
  }
}

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

function InterviewVideoContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id') || (typeof window !== 'undefined' ? localStorage.getItem('prepsense_session_id') : '')
  const [targetRole, setTargetRole] = useState<string>('')
  
  // Briefing vs Active Room state
  const [hasStartedRoom, setHasStartedRoom] = useState<boolean>(false)

  // Interview state
  const [question, setQuestion] = useState<QuestionData | null>(null)
  const [interviewerState, setInterviewerState] = useState<InterviewerState>('IDLE')
  const [loadingInitial, setLoadingInitial] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState<boolean>(false)
  const [sessionStages, setSessionStages] = useState<string[]>([])
  
  // Voice Pipeline state
  const [liveTranscript, setLiveTranscript] = useState<string>('')
  const [isCandidateSpeaking, setIsCandidateSpeaking] = useState<boolean>(false)
  const [wsConnected, setWsConnected] = useState<boolean>(false)
  const [reconnecting, setReconnecting] = useState<boolean>(false)

  // Timer
  const [durationSeconds, setDurationSeconds] = useState(0)

  // Audio refs
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null)
  const audioQueueRef = useRef<AudioPlayerQueue>(new AudioPlayerQueue())
  const isMutedRef = useRef<boolean>(false)
  const reconnectAttemptsRef = useRef<number>(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const maxReconnectAttempts = 5

  useEffect(() => {
    if (!sessionId) {
      router.push('/intake')
      return
    }
    
    // Fetch authoritative role from backend
    api.getSessionState(sessionId).then(res => {
      setTargetRole(res.target_role || 'Software Engineer');
      if (res.stage_order) {
        setSessionStages(res.stage_order);
      }
    }).catch(err => {
      console.warn("Failed to fetch session state, falling back to local storage.", err);
      setTargetRole(localStorage.getItem('prepsense_target_role') || 'Software Engineer');
    });

    return () => {
      cleanupAudio()
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
    }
  }, [sessionId, router])

  useEffect(() => {
    let timer: NodeJS.Timeout
    if (hasStartedRoom && !isComplete) {
      timer = setInterval(() => {
        setDurationSeconds(s => s + 1)
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [hasStartedRoom, isComplete])

  const cleanupAudio = () => {
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    audioQueueRef.current.stopAll();
  }

  const connectWebSocketAndAudio = async () => {
    try {
      // 1. Get Microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true 
        } 
      });
      mediaStreamRef.current = stream;

      // 2. Setup Audio Context (16kHz for consistent wire format)
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;
      
      // Explicitly resume context to unlock browser autoplay restrictions
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }
      
      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(2048, 1, 1);
      scriptProcessorRef.current = processor;

      // Initialize Playback Queue with the unified, resumed context
      audioQueueRef.current.init(audioCtx);

      // 3. Connect WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      let wsHost = window.location.host;
      if (wsHost.includes('3000')) {
          wsHost = wsHost.replace('3000', '8000');
      }
      const wsUrl = `${protocol}//${wsHost}/api/ws/interview/${sessionId}/audio`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        setWsConnected(true);
        setReconnecting(false);
        reconnectAttemptsRef.current = 0;
        // Start streaming audio
        source.connect(processor);
        processor.connect(audioCtx.destination);
      };

      processor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        if (isMutedRef.current) return; // Muted, don't send

        const float32Data = e.inputBuffer.getChannelData(0);
        // Convert float32 to PCM16
        const int16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          let s = Math.max(-1, Math.min(1, float32Data[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        wsRef.current.send(int16Data.buffer);
      };

      ws.onmessage = async (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Received TTS audio chunk (PCM16)
          audioQueueRef.current.addChunk(event.data);
        } else {
          // Control Message
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'state') {
              // Update state mapping
              if (msg.state === 'IDLE' || msg.state === 'LISTENING') setInterviewerState('LISTENING');
              else if (msg.state === 'CANDIDATE_SPEAKING') {
                setInterviewerState('LISTENING');
                setIsCandidateSpeaking(true);
                setLiveTranscript(''); // Clear old transcript on new speech
                audioQueueRef.current.stopAll(); // Interruption! Stop TTS
              }
              else if (msg.state === 'PROCESSING') {
                setInterviewerState('THINKING');
                setIsCandidateSpeaking(false);
              }
              else if (msg.state === 'INTERVIEWER_SPEAKING') setInterviewerState('SPEAKING');
              
              if (msg.state !== 'CANDIDATE_SPEAKING') {
                setIsCandidateSpeaking(false);
              }
            } 
            else if (msg.type === 'transcript') {
              setLiveTranscript(msg.text);
            }
            else if (msg.type === 'dev_speak') {
              // DEV_MODE: use native browser TTS instead of streaming audio
              const utter = new SpeechSynthesisUtterance(msg.text);
              utter.lang = 'en-US';
              utter.rate = 1.0;
              window.speechSynthesis.speak(utter);
            }
            else if (msg.type === 'question') {
              // Emit question to UI
              setQuestion({
                question_id: msg.question_id,
                question_text: msg.text,
                stage: msg.stage,
                topic: msg.topic,
                difficulty: msg.difficulty,
                question_index: msg.question_index,
                total_estimated: msg.total_estimated,
                is_followup: msg.is_followup
              } as QuestionData);
            }
            else if (msg.type === 'completion') {
              setIsComplete(true);
              setTimeout(() => {
                router.push('/practical');
              }, 3000);
            }
            else if (msg.type === 'error') {
              setError(msg.message);
            }
          } catch (e) {
            console.error("WS Message Error:", e);
          }
        }
      };

      ws.onclose = (event) => {
        setWsConnected(false);
        // Bounded exponential backoff reconnect
        if (!isComplete && hasStartedRoom) {
           const retry = () => {
              const count = reconnectAttemptsRef.current;
              if (count >= maxReconnectAttempts) {
                  setError("Connection lost. Your interview progress has been saved.");
                  return;
              }
              setReconnecting(true);
              const delay = Math.min(1000 * Math.pow(2, count), 8000);
              reconnectAttemptsRef.current += 1;
              
              reconnectTimeoutRef.current = setTimeout(() => {
                  if (!isComplete && !wsConnected) {
                      cleanupAudio();
                      connectWebSocketAndAudio();
                  }
              }, delay);
           };
           // Only retry if it was not a clean close or a terminal error
           if (event.code !== 1000 && event.code !== 4001) {
              retry();
           } else if (event.code === 4001) {
              setError("Session invalid, already active, or expired.");
           }
        }
      };
      
      ws.onerror = (e) => {
        console.error("WebSocket error:", e);
      };

    } catch (err: any) {
      setError("Microphone permission denied or Web Audio API not supported. Please allow microphone access.");
      setLoadingInitial(false);
    }
  }

  const handleStartInterviewRoom = async () => {
    if (!sessionId) {
      router.push('/intake')
      return
    }
    setHasStartedRoom(true)
    setLoadingInitial(true)
    reconnectAttemptsRef.current = 0;

    try {
      // Setup Voice Pipeline FIRST
      await connectWebSocketAndAudio();

      // Start the interview session in the backend
      const startRes = await api.startInterview(sessionId)
      setQuestion(startRes.current_question)
      
      // Let backend handle TTS for first question
      setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ type: "play_question", text: startRes.current_question.question_text }));
          }
      }, 500);
      
      setLoadingInitial(false)
    } catch (err: any) {
      setError(err.message || 'Failed to start interview.')
      setLoadingInitial(false)
    }
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#050810] space-y-6">
        <div className="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center">
            <VolumeX className="w-8 h-8 text-rose-500" />
        </div>
        <div className="text-center space-y-2">
            <h2 className="text-xl font-bold text-white">Connection Error</h2>
            <p className="text-sm text-slate-400 max-w-sm">{error}</p>
        </div>
        <button onClick={() => window.location.reload()} className="px-6 py-3 rounded-full bg-slate-800 text-white font-medium hover:bg-slate-700 transition-colors">
          Retry Connection
        </button>
      </div>
    )
  }

  // PRE-INTERVIEW BRIEFING
  if (!hasStartedRoom) {
    return (
      <div className="min-h-screen bg-[#050810] text-slate-200 font-sans selection:bg-emerald-500/30">
        <div className="max-w-4xl mx-auto px-6 py-20 flex flex-col items-center">
            
            <div className="text-emerald-400 font-bold tracking-widest text-sm mb-12 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" /> PREPSENSE
            </div>

            <div className="w-full bg-slate-900 border border-slate-800/60 rounded-3xl p-10 md:p-14 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none translate-x-1/3 -translate-y-1/3" />
                
                <div className="relative z-10 flex flex-col items-center text-center space-y-10">
                    <div className="space-y-4">
                        <h2 className="text-sm text-slate-400 uppercase tracking-widest font-semibold">AI Technical Interview</h2>
                        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight">
                            Your personalized <span className="text-emerald-400">technical interview</span> is ready.
                        </h1>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-3xl border-y border-slate-800/60 py-8 my-8">
                        <div className="flex flex-col items-center space-y-2">
                            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Role</span>
                            <span className="text-slate-200 font-medium">{targetRole}</span>
                        </div>
                        <div className="flex flex-col items-center space-y-2">
                            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Estimated Duration</span>
                            <span className="text-slate-200 font-medium">20–30 minutes</span>
                        </div>
                        <div className="flex flex-col items-center space-y-2">
                            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Voice Mode</span>
                            <span className="text-emerald-400 font-medium flex items-center gap-1.5"><Mic className="w-4 h-4"/> Hands-free</span>
                        </div>
                    </div>
                    
                    <div className="max-w-xl text-sm text-slate-400 bg-slate-950/50 p-6 rounded-2xl border border-slate-800/80">
                        <p>The system listens automatically. No need to click to speak. Please use headphones for the best experience. Microphone access will be requested on the next step.</p>
                    </div>

                    <button
                        onClick={handleStartInterviewRoom}
                        disabled={loadingInitial}
                        className="group flex items-center justify-center gap-3 bg-emerald-600 hover:bg-emerald-500 text-white px-10 py-4 rounded-full font-bold text-lg transition-all shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.4)] disabled:opacity-50"
                    >
                        {loadingInitial ? (
                            <Loader2 className="w-6 h-6 animate-spin" />
                        ) : (
                            <>
                                Start Interview
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
      </div>
    )
  }

  // LIVE INTERVIEW WORKSPACE
  const currentStageIndex = sessionStages.findIndex(s => s === question?.stage)

  return (
    <div className="min-h-screen bg-[#050810] text-slate-200 font-sans flex flex-col">
        {/* TOP NAVIGATION BAR */}
        <header className="h-16 px-6 border-b border-slate-800/60 bg-slate-900/50 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 font-bold tracking-widest text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
                <span className="hidden sm:inline">PREPSENSE</span>
            </div>
            
            <div className="text-sm font-semibold text-slate-300">
                AI Technical Interview
            </div>

            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950 border border-slate-800">
                    <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : reconnecting ? 'bg-amber-500 animate-pulse' : 'bg-rose-500'}`} />
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider hidden sm:inline">
                        {wsConnected ? 'Connected' : reconnecting ? 'Reconnecting' : 'Disconnected'}
                    </span>
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                    <span className="text-xs font-bold text-slate-300">You</span>
                </div>
            </div>
        </header>

        {/* NON-BLOCKING RECONNECT BANNER */}
        {!wsConnected && reconnecting && (
            <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-center gap-3">
                <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
                <span className="text-sm text-amber-400 font-medium">Reconnecting to interview...</span>
            </div>
        )}

        {/* MAIN CONTENT - 3 COLUMN LAYOUT */}
        <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            
            {/* LEFT PANEL - INTERVIEW PROGRESS */}
            <aside className="w-full lg:w-72 shrink-0 border-r border-slate-800/60 bg-slate-950/30 p-6 flex flex-col overflow-y-auto">
                <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-6">Interview Progress</h3>
                
                {question?.question_index !== undefined && question?.total_estimated !== undefined && (
                    <div className="mb-8">
                        <div className="flex justify-between items-end mb-2">
                            <span className="text-sm font-semibold text-white">{question.question_index} of {question.total_estimated} Questions</span>
                            <span className="text-xs text-emerald-400 font-mono">{Math.round((question.question_index / question.total_estimated) * 100)}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-emerald-500 rounded-full transition-all duration-700 ease-out" 
                                style={{ width: `${(question.question_index / question.total_estimated) * 100}%` }}
                            />
                        </div>
                    </div>
                )}

                <div className="space-y-4 mb-8">
                    {sessionStages.length > 0 ? (
                        sessionStages.map((stage, idx) => {
                            const isPast = currentStageIndex > idx
                            const isCurrent = currentStageIndex === idx
                            return (
                                <div key={stage} className={`flex items-center gap-3 text-sm ${isCurrent ? 'text-white font-medium' : isPast ? 'text-slate-500' : 'text-slate-700'}`}>
                                    {isPast ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : isCurrent ? <Play className="w-4 h-4 text-emerald-400 fill-current" /> : <Circle className="w-4 h-4" />}
                                    <span className="capitalize">{stage.replace(/_/g, ' ')}</span>
                                </div>
                            )
                        })
                    ) : (
                        // Fallback generic stages
                        <>
                            <div className={`flex items-center gap-3 text-sm ${question?.stage === 'behavioral' ? 'text-slate-500' : 'text-white font-medium'}`}>
                                {question?.stage === 'behavioral' ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : <Play className="w-4 h-4 text-emerald-400 fill-current" />}
                                <span>Technical Assessment</span>
                            </div>
                            <div className={`flex items-center gap-3 text-sm ${question?.stage === 'behavioral' ? 'text-white font-medium' : 'text-slate-700'}`}>
                                {question?.stage === 'behavioral' ? <Play className="w-4 h-4 text-emerald-400 fill-current" /> : <Circle className="w-4 h-4" />}
                                <span>Behavioral Alignment</span>
                            </div>
                        </>
                    )}
                </div>

                <div className="mt-auto space-y-4 pt-6 border-t border-slate-800/60">
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Duration</span>
                        <span className="text-sm text-slate-300 font-mono flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-slate-500" /> {formatDuration(durationSeconds)}</span>
                    </div>
                    {question?.difficulty && (
                        <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Difficulty</span>
                            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-medium border border-emerald-500/20">{question.difficulty}</span>
                        </div>
                    )}
                </div>
            </aside>

            {/* CENTER - PRIMARY INTERVIEW EXPERIENCE */}
            <section className="flex-1 flex flex-col relative bg-gradient-to-b from-slate-900 via-[#050810] to-[#050810]">
                {/* Voice Status Indicator */}
                <div className="absolute top-6 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-950/80 backdrop-blur border border-slate-800 shadow-lg transition-all duration-300">
                    {interviewerState === 'SPEAKING' && (
                        <>
                            <Volume2 className="w-4 h-4 text-blue-400 animate-pulse" />
                            <span className="text-xs font-semibold text-blue-400">AI is speaking...</span>
                        </>
                    )}
                    {(interviewerState === 'LISTENING' || interviewerState === 'IDLE') && !isCandidateSpeaking && (
                        <>
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                            <span className="text-xs font-semibold text-slate-300">Listening...</span>
                        </>
                    )}
                    {isCandidateSpeaking && (
                        <>
                            <Mic className="w-4 h-4 text-emerald-400 animate-pulse" />
                            <span className="text-xs font-semibold text-emerald-400">Listening to you...</span>
                        </>
                    )}
                    {interviewerState === 'THINKING' && (
                        <>
                            <BrainCircuit className="w-4 h-4 text-purple-400 animate-spin-slow" />
                            <span className="text-xs font-semibold text-purple-400">Analyzing response...</span>
                        </>
                    )}
                </div>

                <div className="flex-1 flex flex-col items-center justify-center p-8 lg:p-12 max-w-4xl mx-auto w-full relative">
                    {/* Avatar Area */}
                    <div className="w-48 h-48 md:w-64 md:h-64 mb-10 shrink-0">
                        <AIInterviewerAvatar state={interviewerState} />
                    </div>

                    {/* Current Question */}
                    <div className="text-center w-full space-y-4 mb-8 flex flex-col items-center justify-center">
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Question</h3>
                        <p className="text-2xl md:text-3xl lg:text-4xl font-medium text-white leading-snug tracking-tight">
                            {question ? question.question_text : "Preparing your next question..."}
                        </p>
                    </div>

                    {/* Candidate Camera (Floating subtly at bottom center/right) */}
                    <div className="absolute bottom-6 right-6 w-48 md:w-56 transition-transform hover:scale-105 z-20">
                        <CandidateCamera isCandidateSpeaking={isCandidateSpeaking} />
                    </div>
                </div>
            </section>

            {/* RIGHT PANEL - INTERVIEW INSIGHTS & TRANSCRIPT */}
            <aside className="w-full lg:w-80 shrink-0 border-l border-slate-800/60 bg-slate-950/30 p-6 flex flex-col overflow-y-auto">
                <div className="mb-10 space-y-6">
                    <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-4">Current Focus</h3>
                    
                    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
                        <div>
                            <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1">Topic</span>
                            <span className="text-sm font-medium text-slate-200">{question?.topic || 'General'}</span>
                        </div>
                        {question?.is_followup && (
                            <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider border border-blue-500/20">
                                <Activity className="w-3 h-3" />
                                Follow-up Question
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex-1 flex flex-col min-h-[200px]">
                    <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-4">Live Transcript</h3>
                    
                    <div className="flex-1 p-4 rounded-xl bg-slate-900/50 border border-slate-800/60 overflow-y-auto space-y-4 relative">
                        {/* Fake fade out at top */}
                        <div className="sticky top-0 h-4 bg-gradient-to-b from-slate-900/50 to-transparent w-full" />
                        
                        {!question && !liveTranscript && (
                            <div className="h-full flex items-center justify-center text-center px-4">
                                <p className="text-sm text-slate-500">Your conversation will appear here.</p>
                            </div>
                        )}

                        {question && (
                            <div className="space-y-1">
                                <span className="text-[10px] font-bold text-slate-500 uppercase">AI Interviewer</span>
                                <p className="text-sm text-slate-300 leading-relaxed">{question.question_text}</p>
                            </div>
                        )}

                        {liveTranscript && (
                            <div className="space-y-1 pt-4 border-t border-slate-800/50">
                                <span className="text-[10px] font-bold text-emerald-500 uppercase">You</span>
                                <p className="text-sm text-slate-300 leading-relaxed">
                                    {liveTranscript.includes('[dev-mode-stub]') 
                                        ? "Audio processed successfully (Simulated transcript for demo purposes)."
                                        : liveTranscript}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </main>

        {/* INTERVIEW COMPLETION OVERLAY */}
        {isComplete && (
            <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-xl flex items-center justify-center p-6 animate-in fade-in duration-700">
                <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-10 md:p-14 text-center shadow-2xl relative overflow-hidden">
                    {/* Glowing background behind success icon */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-emerald-500/20 blur-[100px] rounded-full pointer-events-none" />
                    
                    <div className="relative z-10 flex flex-col items-center space-y-6">
                        <div className="w-24 h-24 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-[0_0_50px_rgba(16,185,129,0.2)]">
                            <Check className="w-12 h-12" />
                        </div>
                        
                        <div className="space-y-3">
                            <h2 className="text-sm text-emerald-400 uppercase tracking-widest font-bold">Interview Complete</h2>
                            <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">Your interview has been completed successfully.</h1>
                        </div>
                        
                        <p className="text-slate-400 max-w-md mx-auto">
                            The AI evaluator has finished the assessment. We are now generating your detailed performance report and transitioning to the practical workspace.
                        </p>

                        <div className="mt-8 pt-8 border-t border-slate-800 w-full flex justify-center">
                            <div className="flex items-center gap-3 text-sm font-medium text-slate-300 bg-slate-950 py-3 px-6 rounded-full border border-slate-800">
                                <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
                                Processing results...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )}
    </div>
  )
}

export default function InterviewPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#050810] flex flex-col items-center justify-center space-y-6">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-sm font-medium text-slate-400 tracking-wide uppercase">Initializing Workspace...</p>
      </div>
    }>
      <InterviewVideoContent />
    </Suspense>
  )
}
