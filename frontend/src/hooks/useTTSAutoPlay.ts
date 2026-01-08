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

// Type for messages that can include date blocks
type MessageOrDateBlock = Message | {
	creation: string
	message_type: 'date'
	name: string
}

/**
 * Hook to auto-play TTS for NEW AI bot messages only.
 * Only triggers for messages that arrive AFTER the initial load.
 *
 * @param messages Array of messages from the chat stream (includes date blocks)
 * @param isBot Whether the current channel is with a bot
 */
export function useTTSAutoPlay(messages: MessageOrDateBlock[] | undefined, isBot: boolean) {
	const ttsEnabled = useAtomValue(TTSEnabledAtom)
	const audioRef = useRef<HTMLAudioElement | null>(null)
	const isPlayingRef = useRef(false)

	// Track the initial message count to only process NEW messages
	const initialMessageCountRef = useRef<number | null>(null)
	const lastProcessedMessageRef = useRef<string | null>(null)

	const { call } = useFrappePostCall<TTSResponse>("nora.api.tts.generate_audio")

	useEffect(() => {
		// Only process if TTS is enabled and this is a bot channel
		if (!ttsEnabled || !isBot) {
			return
		}

		// Filter out date blocks to get only actual messages
		const actualMessages = messages?.filter(
			(m): m is Message => m.message_type !== 'date' && m.message_type !== 'System'
		)

		if (!actualMessages || actualMessages.length === 0) {
			return
		}

		// On first run with messages, store the initial count and don't play anything
		// This ensures we only play TTS for messages that arrive AFTER opening the thread
		if (initialMessageCountRef.current === null) {
			initialMessageCountRef.current = actualMessages.length
			// Mark the latest message as processed so we don't play it
			const latestMessage = actualMessages[actualMessages.length - 1]
			lastProcessedMessageRef.current = latestMessage.name
			console.log("[TTS] Initialized with", actualMessages.length, "messages. Latest:", latestMessage.name)
			return
		}

		// Only process if we have more messages than initial (new message arrived)
		if (actualMessages.length <= initialMessageCountRef.current) {
			return
		}

		// Get the most recent message (messages are sorted oldest-to-newest, so newest is at the end)
		const latestMessage = actualMessages[actualMessages.length - 1]

		// Skip if we've already processed this message
		if (lastProcessedMessageRef.current === latestMessage.name) {
			return
		}

		// Only process bot messages with text content
		// is_bot_message is 1 or 0, not boolean
		if (latestMessage.is_bot_message !== 1 || !latestMessage.text) {
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
		console.log("[TTS] Playing new bot message:", latestMessage.name, "text:", plainText.substring(0, 50))

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
						console.error("[TTS] Audio playback error")
						isPlayingRef.current = false
						audioRef.current = null
					}

					audio.play().catch((error) => {
						console.error("[TTS] Play error:", error)
						isPlayingRef.current = false
						audioRef.current = null
					})
				} else {
					isPlayingRef.current = false
				}
			})
			.catch((error) => {
				console.error("[TTS] API error:", error)
				isPlayingRef.current = false
			})
	}, [messages, isBot, ttsEnabled, call])

	// Reset initial count when channel changes (messages becomes undefined or empty)
	useEffect(() => {
		if (!messages || messages.length === 0) {
			initialMessageCountRef.current = null
			lastProcessedMessageRef.current = null
		}
	}, [messages])

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
