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
 * Clean text for TTS - removes emojis, markdown, HTML tags, etc.
 * Based on Nora's clean_text_for_tts function
 */
function cleanTextForTTS(text: string): string {
	if (!text) return ''

	let cleaned = text

	// Remove ALL emojis (Unicode ranges)
	// Basic Emoji: 1F600-1F64F (emoticons)
	// Misc Symbols: 2600-26FF
	// Dingbats: 2700-27BF
	// Misc Symbols Extended: 1F900-1F9FF
	// Supplemental Symbols: 1F300-1F5FF
	// Transport & Map: 1F680-1F6FF
	cleaned = cleaned.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '')

	// Remove emoji shortcodes like :smile: :thumbsup:
	cleaned = cleaned.replace(/:[a-z_]+:/g, '')

	// Remove HTML tags
	cleaned = cleaned.replace(/<[^>]*>/g, '')

	// Remove Markdown bold/italic markers
	cleaned = cleaned.replace(/\*\*\*/g, '')  // Bold + Italic (***text***)
	cleaned = cleaned.replace(/\*\*/g, '')    // Bold (**text**)
	cleaned = cleaned.replace(/\*/g, '')      // Italic (*text*)
	cleaned = cleaned.replace(/___/g, '')     // Bold + Italic (___text___)
	cleaned = cleaned.replace(/__/g, '')      // Bold (__text__)
	cleaned = cleaned.replace(/_/g, ' ')      // Italic (_text_) - replace with space to avoid joined words

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

	// Track the initial message count to only process NEW messages (per-instance)
	const initialMessageCountRef = useRef<number | null>(null)

	const { call } = useFrappePostCall<TTSResponse>("nora.api.tts.generate_audio")

	useEffect(() => {
		// Debug logging - also show brief toast for debugging in production
		console.log('[TTS AutoPlay] Hook triggered', { ttsEnabled, isBot, messageCount: messages?.length })

		// Show debug indicator in dev/debug mode
		if (typeof window !== 'undefined' && (window as any).__TTS_DEBUG__) {
			const debugDiv = document.createElement('div')
			debugDiv.style.cssText = 'position:fixed;top:10px;right:10px;background:#333;color:#fff;padding:8px;border-radius:4px;z-index:99999;font-size:12px;'
			debugDiv.textContent = `TTS: enabled=${ttsEnabled}, isBot=${isBot}, msgs=${messages?.length}`
			document.body.appendChild(debugDiv)
			setTimeout(() => debugDiv.remove(), 2000)
		}

		// Only process if TTS is enabled and this is a bot channel
		if (!ttsEnabled || !isBot) {
			console.log('[TTS AutoPlay] Skipping - ttsEnabled:', ttsEnabled, 'isBot:', isBot)
			return
		}

		// Filter out date blocks to get only actual messages
		const actualMessages = messages?.filter(
			(m): m is Message => m.message_type !== 'date' && m.message_type !== 'System'
		)

		if (!actualMessages || actualMessages.length === 0) {
			return
		}

		// On first run with messages, store the initial count
		// BUT check if the latest message is a recent bot message (within 30 seconds)
		// This handles the case where a new thread opens and the bot has just responded
		if (initialMessageCountRef.current === null) {
			initialMessageCountRef.current = actualMessages.length
			const latestMessage = actualMessages[actualMessages.length - 1]

			// Check if latest message is a recent bot message that should be played
			if (latestMessage.is_bot_message === 1 && latestMessage.text && globalLastProcessedMessage !== latestMessage.name && !globalIsPlaying) {
				const messageTime = new Date(latestMessage.creation).getTime()
				const now = Date.now()
				const isRecent = (now - messageTime) < 30000

				console.log('[TTS AutoPlay] Initial load with bot message, isRecent:', isRecent, 'age:', now - messageTime, 'ms')

				if (isRecent) {
					// Play TTS for this recent bot message
					globalLastProcessedMessage = latestMessage.name
					globalIsPlaying = true

					const tempDiv = document.createElement("div")
					tempDiv.innerHTML = latestMessage.text
					const rawText = tempDiv.textContent || tempDiv.innerText || ""
					const cleanedText = cleanTextForTTS(rawText)

					if (cleanedText.trim()) {
						console.log('[TTS AutoPlay] Playing initial bot message:', cleanedText.substring(0, 50) + '...')
						call({ text: cleanedText })
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
						globalLastProcessedMessage = latestMessage.name
					}
					return
				}
			}

			// Not a recent bot message, just mark as processed
			globalLastProcessedMessage = latestMessage.name
			console.log('[TTS AutoPlay] Initial load, storing count:', actualMessages.length)
			return
		}

		// Only process if we have more messages than initial (new message arrived)
		if (actualMessages.length <= initialMessageCountRef.current) {
			console.log('[TTS AutoPlay] No new messages, current:', actualMessages.length, 'initial:', initialMessageCountRef.current)
			return
		}

		console.log('[TTS AutoPlay] New message detected! Count:', actualMessages.length, 'vs initial:', initialMessageCountRef.current)

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

		// Extract plain text from HTML content and clean for TTS
		const tempDiv = document.createElement("div")
		tempDiv.innerHTML = latestMessage.text
		const rawText = tempDiv.textContent || tempDiv.innerText || ""

		// Clean text: remove emojis, markdown, etc.
		const cleanedText = cleanTextForTTS(rawText)

		if (!cleanedText.trim()) {
			return
		}

		// Generate and play TTS
		globalIsPlaying = true
		console.log('[TTS AutoPlay] Calling TTS API with text:', cleanedText.substring(0, 50) + '...')

		call({ text: cleanedText })
			.then((response) => {
				// Frappe API wraps response in 'message' key
				const data = (response as any)?.message ?? response
				if (data?.success && data?.audio_url) {
					// Stop any currently playing audio
					if (globalAudio) {
						globalAudio.pause()
						globalAudio = null
					}

					const audio = new Audio(data.audio_url)
					globalAudio = audio
					console.log('[TTS AutoPlay] Audio created, attempting to play:', data.audio_url)

					audio.onended = () => {
						console.log('[TTS AutoPlay] Audio playback ended')
						globalIsPlaying = false
						globalAudio = null
					}

					audio.onerror = () => {
						globalIsPlaying = false
						globalAudio = null
					}

					audio.play().catch((error) => {
						console.error('[TTS AutoPlay] Failed to play audio:', error.name, error.message)
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

	// Track previous isBot value to detect transitions
	const previousIsBotRef = useRef<boolean>(isBot)

	// Reset initial count when channel changes (messages becomes undefined or empty)
	// OR when isBot transitions from false to true (e.g., when channelMembers loads)
	useEffect(() => {
		if (!messages || messages.length === 0) {
			initialMessageCountRef.current = null
		}
	}, [messages])

	// Handle when isBot changes from false to true
	// This handles the case where channelMembers loads AFTER messages (e.g., new thread creation)
	useEffect(() => {
		if (isBot && !previousIsBotRef.current && ttsEnabled) {
			console.log('[TTS AutoPlay] isBot transitioned to true, checking for recent bot message')

			// Filter to actual messages
			const actualMessages = messages?.filter(
				(m): m is Message => m.message_type !== 'date' && m.message_type !== 'System'
			)

			console.log('[TTS AutoPlay] Messages available:', actualMessages?.length ?? 0, 'messages:', actualMessages?.map(m => ({ name: m.name, is_bot: m.is_bot_message, owner: m.owner })))

			if (actualMessages && actualMessages.length > 0) {
				// Find the most recent bot message
				const latestBotMessage = [...actualMessages].reverse().find(m => m.is_bot_message === 1 && m.text)
				console.log('[TTS AutoPlay] Latest bot message found:', latestBotMessage ? latestBotMessage.name : 'none')

				if (latestBotMessage && globalLastProcessedMessage !== latestBotMessage.name && !globalIsPlaying) {
					// Check if this message is recent (within last 30 seconds)
					const messageTime = new Date(latestBotMessage.creation).getTime()
					const now = Date.now()
					const isRecent = (now - messageTime) < 30000

					console.log('[TTS AutoPlay] Found bot message, isRecent:', isRecent, 'age:', now - messageTime, 'ms')

					if (isRecent) {
						// Play TTS for this message
						globalLastProcessedMessage = latestBotMessage.name
						globalIsPlaying = true

						const tempDiv = document.createElement("div")
						tempDiv.innerHTML = latestBotMessage.text
						const rawText = tempDiv.textContent || tempDiv.innerText || ""
						const cleanedText = cleanTextForTTS(rawText)

						if (cleanedText.trim()) {
							console.log('[TTS AutoPlay] Playing missed bot message:', cleanedText.substring(0, 50) + '...')
							call({ text: cleanedText })
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

				// Set initial count to current so future messages trigger normally
				initialMessageCountRef.current = actualMessages.length
			}
		}
		previousIsBotRef.current = isBot
	}, [isBot, ttsEnabled, messages, call])

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
