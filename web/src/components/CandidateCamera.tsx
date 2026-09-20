'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Camera, CameraOff, User } from 'lucide-react'

interface CandidateCameraProps {
  isCandidateSpeaking?: boolean
}

export function CandidateCamera({ isCandidateSpeaking = false }: CandidateCameraProps) {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isCameraOn, setIsCameraOn] = useState<boolean>(true)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)

  useEffect(() => {
    let activeStream: MediaStream | null = null

    const initMedia = async () => {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          const s = await navigator.mediaDevices.getUserMedia({
            video: { 
              width: { ideal: 1280 }, 
              height: { ideal: 720 },
              frameRate: { ideal: 30, max: 30 }
            },
            audio: false
          })
          activeStream = s
          setStream(s)
          setHasPermission(true)
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
    if (stream) {
      const videoTracks = stream.getVideoTracks()
      videoTracks.forEach(track => {
        track.enabled = !isCameraOn
      })
      setIsCameraOn(!isCameraOn)
    }
  }

  return (
    <div className={`relative w-full aspect-video rounded-2xl overflow-hidden bg-slate-900 border transition-all duration-300 shadow-xl ${
      isCandidateSpeaking ? 'border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.2)]' : 'border-slate-800/80'
    }`}>
      {hasPermission && isCameraOn ? (
        <video
          ref={(node) => {
            if (node && stream) {
              node.srcObject = stream
            }
          }}
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

      {/* Floating Name Badge and LIVE indicator */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
        <div className="px-3 py-1 rounded-full bg-slate-900/60 backdrop-blur-md border border-slate-700/50 text-[11px] font-medium text-slate-200 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isCandidateSpeaking ? 'bg-blue-400 animate-pulse' : 'bg-slate-500'}`} />
          <span>You</span>
        </div>
        {hasPermission && isCameraOn && (
          <div className="px-2 py-1 rounded-full bg-rose-500/20 border border-rose-500/30 text-[10px] font-bold text-rose-400 tracking-wider flex items-center gap-1.5 uppercase">
            <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            Live Camera
          </div>
        )}
      </div>

      {/* Floating Controls */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
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
