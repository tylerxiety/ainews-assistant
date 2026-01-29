import { useCallback, useEffect, useRef, useState } from 'react'
import { MicVAD } from '@ricky0123/vad-web'
import { API_URL } from '../lib/api'
import { CONFIG } from '../config'
import vadModelUrl from '@ricky0123/vad-web/dist/silero_vad.onnx?url'
import vadWorkletUrl from '@ricky0123/vad-web/dist/vad.worklet.bundle.min.js?url'
import pcmWorkletUrl from '../worklets/pcm-capture.worklet.js?url'

export interface VoiceCommand {
  name: string
  args: Record<string, unknown>
}

interface UseVoiceModeOptions {
  issueId?: string
  onCommand: (command: VoiceCommand) => void
  onSpeechStart: () => void
  onSpeechEnd: () => void
  onTranscript: (text: string) => void
  onAnswerStart: () => void
  onAnswerEnd: () => void
  onError: (message: string) => void
}

interface VoiceModeState {
  isVoiceModeActive: boolean
  isListening: boolean
  isSpeaking: boolean
  isProcessing: boolean
  lastCommand: string | null
  toggleVoiceMode: () => void
  stopVoiceMode: () => void
}

const OUTPUT_SAMPLE_RATE = 24000
const MAX_WS_BUFFER_SIZE = 256 * 1024 // 256KB - prevent backpressure buildup

function buildWsUrl(path: string) {
  if (API_URL) {
    const wsBase = API_URL.replace(/^http/, 'ws')
    return `${wsBase}${path}`
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${path}`
}

export function useVoiceMode(options: UseVoiceModeOptions): VoiceModeState {
  const {
    issueId,
    onCommand,
    onSpeechStart,
    onSpeechEnd,
    onTranscript,
    onAnswerStart,
    onAnswerEnd,
    onError,
  } = options

  const [isVoiceModeActive, setIsVoiceModeActive] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastCommand, setLastCommand] = useState<string | null>(null)

  const audioContextRef = useRef<AudioContext | null>(null)
  const workletNodeRef = useRef<AudioWorkletNode | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const vadRef = useRef<MicVAD | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const playbackTimeRef = useRef(0)
  const playbackTimerRef = useRef<number | null>(null)
  const resumptionHandleRef = useRef<string | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const shouldReconnectRef = useRef(false)
  const assistantSpeakingRef = useRef(false)

  const ensureAudioContextRunning = useCallback(async () => {
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume()
    }
  }, [])

  const handleAudioChunk = useCallback(
    async (chunk: ArrayBuffer) => {
      const audioContext = audioContextRef.current
      if (!audioContext) return

      await ensureAudioContextRunning()
      const pcm = new Int16Array(chunk)
      const buffer = audioContext.createBuffer(1, pcm.length, OUTPUT_SAMPLE_RATE)
      const channel = buffer.getChannelData(0)
      for (let i = 0; i < pcm.length; i += 1) {
        channel[i] = pcm[i] / 0x7fff
      }

      const source = audioContext.createBufferSource()
      source.buffer = buffer
      source.connect(audioContext.destination)

      const startTime = Math.max(audioContext.currentTime, playbackTimeRef.current)
      source.start(startTime)
      playbackTimeRef.current = startTime + buffer.duration

      if (!assistantSpeakingRef.current) {
        assistantSpeakingRef.current = true
        setIsProcessing(false)
        onAnswerStart()
      }

      if (playbackTimerRef.current) {
        window.clearTimeout(playbackTimerRef.current)
      }

      const timeUntilEnd = Math.max(
        0,
        (playbackTimeRef.current - audioContext.currentTime) * 1000
      )
      playbackTimerRef.current = window.setTimeout(() => {
        assistantSpeakingRef.current = false
        onAnswerEnd()
      }, timeUntilEnd + 120)
    },
    [ensureAudioContextRunning, onAnswerEnd, onAnswerStart]
  )

  const handleServerMessage = useCallback(
    (message: string) => {
      try {
        const data = JSON.parse(message)

        if (data.type === 'tool_call') {
          const name = String(data.name || '')
          setLastCommand(name || null)
          setIsProcessing(false)
          onCommand({ name, args: data.args || {} })
          return
        }

        if (data.type === 'transcript') {
          setIsProcessing(false)
          onTranscript(String(data.text || ''))
          return
        }

        if (data.type === 'session_resumption') {
          if (data.handle) {
            resumptionHandleRef.current = String(data.handle)
          }
          return
        }

        if (data.type === 'go_away') {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close()
          }
          return
        }

        if (data.type === 'error') {
          onError(String(data.message || 'Voice session error'))
        }
      } catch (err) {
        onError('Failed to parse voice server message.')
      }
    },
    [onCommand, onError, onTranscript]
  )

  const connectWebSocket = useCallback(async () => {
    if (!issueId) {
      onError('Voice mode requires a valid issue.')
      return
    }

    const wsUrl = buildWsUrl(`/ws/voice/${issueId}`)
    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => {
      setIsListening(true)
      if (resumptionHandleRef.current) {
        ws.send(
          JSON.stringify({ type: 'start', resumeHandle: resumptionHandleRef.current })
        )
      } else {
        ws.send(JSON.stringify({ type: 'start' }))
      }
    }

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        handleServerMessage(event.data)
        return
      }
      if (event.data instanceof ArrayBuffer) {
        handleAudioChunk(event.data)
      }
    }

    ws.onerror = () => {
      onError('Voice mode connection error.')
    }

    ws.onclose = () => {
      setIsListening(false)
      if (shouldReconnectRef.current) {
        if (reconnectTimerRef.current) {
          window.clearTimeout(reconnectTimerRef.current)
        }
        reconnectTimerRef.current = window.setTimeout(() => {
          connectWebSocket().catch(() => undefined)
        }, 1000)
      }
    }
  }, [handleAudioChunk, handleServerMessage, issueId, onError])

  const stopVoiceMode = useCallback(() => {
    shouldReconnectRef.current = false
    setIsVoiceModeActive(false)
    setIsListening(false)
    setIsSpeaking(false)
    setIsProcessing(false)
    setLastCommand(null)

    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    if (playbackTimerRef.current) {
      window.clearTimeout(playbackTimerRef.current)
      playbackTimerRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    if (vadRef.current) {
      vadRef.current.pause()
      vadRef.current = null
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect()
      workletNodeRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
  }, [])

  const startVoiceMode = useCallback(async () => {
    if (!issueId) {
      onError('Voice mode requires a valid issue.')
      return
    }

    setIsVoiceModeActive(true)
    shouldReconnectRef.current = true

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      onError('Microphone access requires HTTPS or localhost.')
      stopVoiceMode()
      return
    }

    try {
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      await audioContext.resume()
      playbackTimeRef.current = audioContext.currentTime
      try {
        await audioContext.audioWorklet.addModule(pcmWorkletUrl)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        throw new Error(`PCM worklet failed to load (${pcmWorkletUrl}): ${message}`)
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream

      const source = audioContext.createMediaStreamSource(stream)
      const workletNode = new AudioWorkletNode(audioContext, 'pcm-capture')
      const zeroGain = audioContext.createGain()
      zeroGain.gain.value = 0
      source.connect(workletNode).connect(zeroGain).connect(audioContext.destination)

      workletNode.port.onmessage = (event) => {
        const ws = wsRef.current
        if (ws && ws.readyState === WebSocket.OPEN) {
          if (ws.bufferedAmount > MAX_WS_BUFFER_SIZE) {
            return
          }
          ws.send(event.data)
        }
      }

      workletNodeRef.current = workletNode

      const vadSensitivity = CONFIG.voiceMode.vadSensitivity
      const vad = await MicVAD.new({
        stream,
        workletURL: vadWorkletUrl,
        modelURL: vadModelUrl,
        ortConfig: (ort) => {
          ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.23.2/dist/'
          ort.env.wasm.numThreads = 1
        },
        onSpeechStart: () => {
          setIsSpeaking(true)
          setIsProcessing(false)
          onSpeechStart()
        },
        onSpeechEnd: () => {
          setIsSpeaking(false)
          setIsProcessing(true)
          onSpeechEnd()
        },
        positiveSpeechThreshold: vadSensitivity.positiveSpeechThreshold,
        negativeSpeechThreshold: vadSensitivity.negativeSpeechThreshold,
        minSpeechFrames: vadSensitivity.minSpeechFrames,
      })
      vadRef.current = vad
      vad.start()

      await connectWebSocket()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      if (import.meta.env.DEV) {
        console.error('Voice mode startup failed:', err)
      }
      onError(`Failed to start voice mode. ${message}`)
      stopVoiceMode()
    }
  }, [connectWebSocket, issueId, onError, onSpeechEnd, onSpeechStart, stopVoiceMode])

  const toggleVoiceMode = useCallback(() => {
    if (isVoiceModeActive) {
      stopVoiceMode()
    } else {
      startVoiceMode().catch(() => undefined)
    }
  }, [isVoiceModeActive, startVoiceMode, stopVoiceMode])

  useEffect(() => {
    return () => {
      stopVoiceMode()
    }
  }, [stopVoiceMode])

  useEffect(() => {
    if (!isVoiceModeActive) return

    const timeoutId = window.setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }, CONFIG.voiceMode.sessionTimeoutMs)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [isVoiceModeActive])

  useEffect(() => {
    if (!isVoiceModeActive) return

    const handleInteraction = () => {
      ensureAudioContextRunning().catch(() => undefined)
    }

    window.addEventListener('click', handleInteraction)
    window.addEventListener('touchend', handleInteraction)

    return () => {
      window.removeEventListener('click', handleInteraction)
      window.removeEventListener('touchend', handleInteraction)
    }
  }, [ensureAudioContextRunning, isVoiceModeActive])

  return {
    isVoiceModeActive,
    isListening,
    isSpeaking,
    isProcessing,
    lastCommand,
    toggleVoiceMode,
    stopVoiceMode,
  }
}
