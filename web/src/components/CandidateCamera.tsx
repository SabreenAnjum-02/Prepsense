'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Camera, CameraOff, Mic, MicOff, User } from 'lucide-react'

interface CandidateCameraProps {
  isCandidateSpeaking?: boolean
}

export function CandidateCamera({ isCandidateSpeaking = false }: CandidateCameraProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isCameraOn, setIsCameraOn] = useState<boolean>(true)
  const [isMicOn, setIsMicOn] = useState<boolean>(true)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)

  useEffect(() => {
    let activeStream: MediaStream | null = null

    const initMedia = async () => {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const s = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 360 } },
            audio: true
          })
          activeStream = s
          setStream(s)
          setHasPermission(true)

          if (videoRef.current) {
            videoRef.current.srcObject = s
          }
        }
      } catch (err) {
        console.warn('Webcam permission not granted or unavailable:', err)
        setHasPermission(false)
      }
    }

    initMedia()

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const toggleCamera = () => {
    if (!stream) return
    const videoTracks = stream.getVideoTracks()
    if (videoTracks.length > 0) {
      videoTracks[0].enabled = !videoTracks[0].enabled
      setIsCameraOn(videoTracks[0].enabled)
    }
  }

  const toggleMic = () => {
    if (!stream) return
    const audioTracks = stream.getAudioTracks()
    if (audioTracks.length > 0) {
      audioTracks[0].enabled = !audioTracks[0].enabled
      setIsMicOn(audioTracks[0].enabled)
    }
  }

  return (
    <div className={`relative w-full aspect-video rounded-2xl overflow-hidden bg-slate-900 border transition-all duration-300 shadow-xl ${
      isCandidateSpeaking ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'border-slate-800/80'
    }`}>
      {hasPermission && isCameraOn ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover transform -scale-x-100"
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center space-y-2 bg-slate-950 text-slate-500">
          <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
            <User className="w-6 h-6 text-slate-600" />
          </div>
        </div>
      )}

      {/* Floating Name Badge */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
        <div className="px-3 py-1 rounded-full bg-slate-900/60 backdrop-blur-md border border-slate-700/50 text-[11px] font-medium text-slate-200 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isCandidateSpeaking ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
          <span>You</span>
        </div>
      </div>

      {/* Floating Controls */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMic}
          className={`p-2 rounded-full backdrop-blur-md transition-colors ${
            isMicOn ? 'bg-slate-900/40 text-white hover:bg-slate-900/60' : 'bg-rose-500/80 text-white'
          }`}
        >
          {isMicOn ? <Mic className="w-3.5 h-3.5" /> : <MicOff className="w-3.5 h-3.5" />}
        </button>

        <button
          type="button"
          onClick={toggleCamera}
          className={`p-2 rounded-full backdrop-blur-md transition-colors ${
            isCameraOn ? 'bg-slate-900/40 text-white hover:bg-slate-900/60' : 'bg-rose-500/80 text-white'
          }`}
        >
          {isCameraOn ? <Camera className="w-3.5 h-3.5" /> : <CameraOff className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  )
}
