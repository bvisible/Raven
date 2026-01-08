import { useEffect, useRef } from "react"
import { useAtomValue } from "jotai"
import { useFrappePostCall } from "frappe-react-sdk"
import { TTSEnabledAtom, TTSVoiceAtom } from "@/utils/preferences"
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
 * Clean text for TTS - removes emojis, markdown, HTML tags, etc.
 */
function cleanTextForTTS(text: string): string {
	if (!text) return ''

	let cleaned = text

	// Remove ALL emojis (Unicode ranges)
	cleaned = cleaned.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '')

	// Remove emoji shortcodes like :smile: :thumbsup:
	cleaned = cleaned.replace(/:[a-z_]+:/g, '')

	// Remove HTML tags
	cleaned = cleaned.replace(/<[^>]*>/g, '')

	// Remove Markdown bold/italic markers
	cleaned = cleaned.replace(/\*\*\*/g, '')
	cleaned = cleaned.replace(/\*\*/g, '')
	cleaned = cleaned.replace(/\*/g, '')
	cleaned = cleaned.replace(/___/g, '')
	cleaned = cleaned.replace(/__/g, '')
	cleaned = cleaned.replace(/_/g, ' ')

	// Remove Markdown links but keep the text: [text](url) -> text
	cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

	// Remove Markdown headers (#, ##, etc.)
	cleaned = cleaned.replace(/^#{1,6}\s+/gm, '')

	// Remove Markdown code blocks (``` or `)
	cleaned = cleaned.replace(/```[^`]*```/g, '')
	cleaned = cleaned.replace(/`([^`]+)`/g, '$1')

	// Remove Markdown lists (-, *, +, numbers)
	cleaned = cleaned.replace(/^\s*[-*+]\s+/gm, '')
	cleaned = cleaned.replace(/^\s*\d+\.\s+/gm, '')

	// Decode common HTML entities
	cleaned = cleaned.replace(/&nbsp;/g, ' ')
	cleaned = cleaned.replace(/&amp;/g, '&')
	cleaned = cleaned.replace(/&lt;/g, '<')
	cleaned = cleaned.replace(/&gt;/g, '>')
	cleaned = cleaned.replace(/&quot;/g, '"')
	cleaned = cleaned.replace(/&#39;/g, "'")

	// Remove extra whitespace
	cleaned = cleaned.replace(/\s+/g, ' ').trim()

	return cleaned
}

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
	const ttsVoice = useAtomValue(TTSVoiceAtom)

	// Track the initial message count to only process NEW messages (per-instance)
	const initialMessageCountRef = useRef<number | null>(null)

	// Track when we started waiting for messages (when isBot became true with empty messages)
	const waitingForMessagesSinceRef = useRef<number | null>(null)

	const { call } = useFrappePostCall<TTSResponse>("nora.api.tts.generate_audio")

	useEffect(() => {
		if (!ttsEnabled || !isBot) {
			return
		}

		const actualMessages = messages?.filter(
			(m): m is Message => m.message_type !== 'date' && m.message_type !== 'System'
		)

		if (!actualMessages || actualMessages.length === 0) {
			return
		}

		// On first run with messages, store the initial count and check for recent bot message
		if (initialMessageCountRef.current === null) {
			initialMessageCountRef.current = actualMessages.length

			const latestBotMessage = [...actualMessages].reverse().find(m => m.is_bot_message === 1 && m.text)
			const latestMessage = actualMessages[actualMessages.length - 1]

			if (latestBotMessage && globalLastProcessedMessage !== latestBotMessage.name && !globalIsPlaying) {
				const messageTime = new Date(latestBotMessage.creation).getTime()
				const now = Date.now()
				const ageMs = now - messageTime

				const wasWaitingForMessages = waitingForMessagesSinceRef.current !== null
				const arrivedAfterWaiting = wasWaitingForMessages && messageTime >= waitingForMessagesSinceRef.current!
				const isRecent = ageMs < 30000 || arrivedAfterWaiting

				waitingForMessagesSinceRef.current = null

				if (isRecent) {
					globalLastProcessedMessage = latestBotMessage.name
					globalIsPlaying = true

					const tempDiv = document.createElement("div")
					tempDiv.innerHTML = latestBotMessage.text
					const rawText = tempDiv.textContent || tempDiv.innerText || ""
					const cleanedText = cleanTextForTTS(rawText)

					if (cleanedText.trim()) {
						call({ text: cleanedText, voice: ttsVoice })
							.then((response) => {
								const data = (response as any)?.message ?? response
								if (data?.success && data?.audio_url) {
									if (globalAudio) {
										globalAudio.pause()
										globalAudio = null
									}
									const audio = new Audio(data.audio_url)
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
					} else {
						globalIsPlaying = false
					}
					globalLastProcessedMessage = latestMessage.name
					return
				}
			}

			globalLastProcessedMessage = latestMessage.name
			waitingForMessagesSinceRef.current = null
			return
		}

		// Only process if we have more messages than initial (new message arrived)
		if (actualMessages.length <= initialMessageCountRef.current) {
			return
		}

		const latestMessage = actualMessages[actualMessages.length - 1]

		if (globalLastProcessedMessage === latestMessage.name) {
			return
		}

		if (latestMessage.is_bot_message !== 1 || !latestMessage.text) {
			globalLastProcessedMessage = latestMessage.name
			return
		}

		if (globalIsPlaying) {
			return
		}

		globalLastProcessedMessage = latestMessage.name

		const tempDiv = document.createElement("div")
		tempDiv.innerHTML = latestMessage.text
		const rawText = tempDiv.textContent || tempDiv.innerText || ""
		const cleanedText = cleanTextForTTS(rawText)

		if (!cleanedText.trim()) {
			return
		}

		globalIsPlaying = true

		call({ text: cleanedText, voice: ttsVoice })
			.then((response) => {
				const data = (response as any)?.message ?? response
				if (data?.success && data?.audio_url) {
					if (globalAudio) {
						globalAudio.pause()
						globalAudio = null
					}

					const audio = new Audio(data.audio_url)
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
	}, [messages, isBot, ttsEnabled, ttsVoice, call])

	const previousIsBotRef = useRef<boolean>(isBot)

	useEffect(() => {
		if (!messages || messages.length === 0) {
			initialMessageCountRef.current = null
		}
	}, [messages])

	// Handle when isBot changes from false to true
	useEffect(() => {
		if (isBot && !previousIsBotRef.current && ttsEnabled) {
			const actualMessages = messages?.filter(
				(m): m is Message => m.message_type !== 'date' && m.message_type !== 'System'
			)

			if (!actualMessages || actualMessages.length === 0) {
				waitingForMessagesSinceRef.current = Date.now()
			} else if (actualMessages && actualMessages.length > 0) {
				waitingForMessagesSinceRef.current = null
				const latestBotMessage = [...actualMessages].reverse().find(m => m.is_bot_message === 1 && m.text)

				if (latestBotMessage && globalLastProcessedMessage !== latestBotMessage.name && !globalIsPlaying) {
					const messageTime = new Date(latestBotMessage.creation).getTime()
					const now = Date.now()
					const isRecent = (now - messageTime) < 30000

					if (isRecent) {
						globalLastProcessedMessage = latestBotMessage.name
						globalIsPlaying = true

						const tempDiv = document.createElement("div")
						tempDiv.innerHTML = latestBotMessage.text
						const rawText = tempDiv.textContent || tempDiv.innerText || ""
						const cleanedText = cleanTextForTTS(rawText)

						if (cleanedText.trim()) {
							call({ text: cleanedText, voice: ttsVoice })
								.then((response) => {
									const data = (response as any)?.message ?? response
									if (data?.success && data?.audio_url) {
										if (globalAudio) {
											globalAudio.pause()
											globalAudio = null
										}
										const audio = new Audio(data.audio_url)
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
						} else {
							globalIsPlaying = false
						}
					}
				}

				initialMessageCountRef.current = actualMessages.length
			}
		}
		previousIsBotRef.current = isBot
	}, [isBot, ttsEnabled, ttsVoice, messages, call])

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
