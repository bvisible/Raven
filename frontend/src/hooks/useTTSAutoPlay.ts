import { useEffect, useRef } from "react"
import { useAtomValue } from "jotai"
import { useFrappePostCall } from "frappe-react-sdk"
import { TTSEnabledAtom } from "@/utils/preferences"
import { Message } from "../../../../types/Messaging/Message"

interface TTSResponse {
	success: boolean
	audio_url?: string
	duration_ms?: number
	error?: string
}

/**
 * Hook to auto-play TTS for new AI bot messages.
 * Monitors messages array and plays audio when a new bot message arrives.
 *
 * @param messages Array of messages from the chat stream
 * @param isBot Whether the current channel is with a bot
 */
export function useTTSAutoPlay(messages: Message[] | undefined, isBot: boolean) {
	const ttsEnabled = useAtomValue(TTSEnabledAtom)
	const lastProcessedMessageRef = useRef<string | null>(null)
	const audioRef = useRef<HTMLAudioElement | null>(null)
	const isPlayingRef = useRef(false)

	const { call } = useFrappePostCall<TTSResponse>("nora.api.tts.generate_audio")

	useEffect(() => {
		// Only process if TTS is enabled, this is a bot channel, and we have messages
		if (!ttsEnabled || !isBot || !messages || messages.length === 0) {
			return
		}

		// Get the most recent message (messages are sorted by creation desc, so newest is at index 0)
		const latestMessage = messages[0]

		// Skip if we've already processed this message
		if (lastProcessedMessageRef.current === latestMessage.name) {
			return
		}

		// Only process bot messages with text content
		if (!latestMessage.is_bot_message || !latestMessage.text) {
			lastProcessedMessageRef.current = latestMessage.name
			return
		}

		// Skip if audio is already playing
		if (isPlayingRef.current) {
			return
		}

		// Mark as processed
		lastProcessedMessageRef.current = latestMessage.name

		// Extract plain text from HTML content
		const tempDiv = document.createElement("div")
		tempDiv.innerHTML = latestMessage.text
		const plainText = tempDiv.textContent || tempDiv.innerText || ""

		if (!plainText.trim()) {
			return
		}

		// Generate and play TTS
		isPlayingRef.current = true

		call({ text: plainText })
			.then((response) => {
				if (response?.success && response?.audio_url) {
					// Stop any currently playing audio
					if (audioRef.current) {
						audioRef.current.pause()
						audioRef.current = null
					}

					const audio = new Audio(response.audio_url)
					audioRef.current = audio

					audio.onended = () => {
						isPlayingRef.current = false
						audioRef.current = null
					}

					audio.onerror = () => {
						console.error("TTS audio playback error")
						isPlayingRef.current = false
						audioRef.current = null
					}

					audio.play().catch((error) => {
						console.error("TTS play error:", error)
						isPlayingRef.current = false
						audioRef.current = null
					})
				} else {
					isPlayingRef.current = false
				}
			})
			.catch((error) => {
				console.error("TTS API error:", error)
				isPlayingRef.current = false
			})
	}, [messages, isBot, ttsEnabled, call])

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			if (audioRef.current) {
				audioRef.current.pause()
				audioRef.current = null
			}
		}
	}, [])
}
