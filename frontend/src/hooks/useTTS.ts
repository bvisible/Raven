import { useCallback, useRef, useState } from "react"
import { useAtom, useAtomValue } from "jotai"
import { useFrappePostCall } from "frappe-react-sdk"
import { TTSEnabledAtom, TTSVoiceAtom } from "@/utils/preferences"

interface TTSResponse {
	success: boolean
	audio_url?: string
	duration_ms?: number
	error?: string
}

interface UseTTSReturn {
	isPlaying: boolean
	isLoading: boolean
	generateAndPlay: (text: string) => Promise<void>
	stop: () => void
	ttsEnabled: boolean
	setTTSEnabled: (enabled: boolean) => void
}

/**
 * Hook for Text-to-Speech functionality using Nora's TTS API.
 * Uses edge-tts with Microsoft Neural voices on the backend.
 *
 * @returns TTS controls and state
 */
export function useTTS(): UseTTSReturn {
	const [ttsEnabled, setTTSEnabled] = useAtom(TTSEnabledAtom)
	const ttsVoice = useAtomValue(TTSVoiceAtom)
	const [isPlaying, setIsPlaying] = useState(false)
	const [isLoading, setIsLoading] = useState(false)
	const audioRef = useRef<HTMLAudioElement | null>(null)

	const { call } = useFrappePostCall<TTSResponse>("nora.api.tts.generate_audio")

	const stop = useCallback(() => {
		if (audioRef.current) {
			audioRef.current.pause()
			audioRef.current.currentTime = 0
			audioRef.current = null
		}
		setIsPlaying(false)
	}, [])

	const generateAndPlay = useCallback(async (text: string) => {
		if (!text.trim()) return

		// Stop any currently playing audio
		stop()

		setIsLoading(true)

		try {
			const response = await call({ text, voice: ttsVoice })

			if (response?.success && response?.audio_url) {
				const audio = new Audio(response.audio_url)
				audioRef.current = audio

				audio.onplay = () => {
					setIsPlaying(true)
					setIsLoading(false)
				}

				audio.onended = () => {
					setIsPlaying(false)
					audioRef.current = null
				}

				audio.onerror = () => {
					console.error("TTS audio playback error")
					setIsPlaying(false)
					setIsLoading(false)
					audioRef.current = null
				}

				await audio.play()
			} else {
				console.error("TTS generation failed:", response?.error)
				setIsLoading(false)
			}
		} catch (error) {
			console.error("TTS API error:", error)
			setIsLoading(false)
		}
	}, [call, stop, ttsVoice])

	return {
		isPlaying,
		isLoading,
		generateAndPlay,
		stop,
		ttsEnabled,
		setTTSEnabled
	}
}
