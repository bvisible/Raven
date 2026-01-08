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

// Module-level state to prevent multiple instances from playing simultaneously
let globalIsPlaying = false
let globalLastProcessedMessage: string | null = null
let globalAudio: HTMLAudioElement | null = null

/**
 * Hook to auto-play TTS for NEW AI bot messages only.
 * Only triggers for messages that arrive AFTER the initial load.
 * Uses module-level state to prevent multiple component instances from playing simultaneously.
 *
 * @param messages Array of messages from the chat stream (includes date blocks)
 * @param isBot Whether the current channel is with a bot
 */
export function useTTSAutoPlay(messages: MessageOrDateBlock[] | undefined, isBot: boolean) {
	const ttsEnabled = useAtomValue(TTSEnabledAtom)

	// Track the initial message count to only process NEW messages (per-instance)
	const initialMessageCountRef = useRef<number | null>(null)

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
			// Mark the latest message as processed globally so we don't play it
			const latestMessage = actualMessages[actualMessages.length - 1]
			globalLastProcessedMessage = latestMessage.name
			return
		}

		// Only process if we have more messages than initial (new message arrived)
		if (actualMessages.length <= initialMessageCountRef.current) {
			return
		}

		// Get the most recent message (messages are sorted oldest-to-newest, so newest is at the end)
		const latestMessage = actualMessages[actualMessages.length - 1]

		// Skip if we've already processed this message (global check across all instances)
		if (globalLastProcessedMessage === latestMessage.name) {
			return
		}

		// Only process bot messages with text content
		// is_bot_message is 1 or 0, not boolean
		if (latestMessage.is_bot_message !== 1 || !latestMessage.text) {
			globalLastProcessedMessage = latestMessage.name
			return
		}

		// Skip if audio is already playing globally (across all instances)
		if (globalIsPlaying) {
			return
		}

		// Mark as processed globally
		globalLastProcessedMessage = latestMessage.name

		// Extract plain text from HTML content
		const tempDiv = document.createElement("div")
		tempDiv.innerHTML = latestMessage.text
		const plainText = tempDiv.textContent || tempDiv.innerText || ""

		if (!plainText.trim()) {
			return
		}

		// Generate and play TTS
		globalIsPlaying = true

		call({ text: plainText })
			.then((response) => {
				if (response?.success && response?.audio_url) {
					// Stop any currently playing audio
					if (globalAudio) {
						globalAudio.pause()
						globalAudio = null
					}

					const audio = new Audio(response.audio_url)
					globalAudio = audio

					audio.onended = () => {
						globalIsPlaying = false
						globalAudio = null
					}

					audio.onerror = () => {
						globalIsPlaying = false
						globalAudio = null
					}

					audio.play().catch(() => {
						globalIsPlaying = false
						globalAudio = null
					})
				} else {
					globalIsPlaying = false
				}
			})
			.catch(() => {
				globalIsPlaying = false
			})
	}, [messages, isBot, ttsEnabled, call])

	// Reset initial count when channel changes (messages becomes undefined or empty)
	useEffect(() => {
		if (!messages || messages.length === 0) {
			initialMessageCountRef.current = null
		}
	}, [messages])

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			if (globalAudio) {
				globalAudio.pause()
				globalAudio = null
			}
			globalIsPlaying = false
		}
	}, [])
}
