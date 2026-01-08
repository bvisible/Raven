import { useCallback, useRef, useState, useEffect } from "react"

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
	results: SpeechRecognitionResultList
	resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
	error: string
	message?: string
}

interface SpeechRecognition extends EventTarget {
	continuous: boolean
	interimResults: boolean
	lang: string
	start(): void
	stop(): void
	abort(): void
	onresult: ((event: SpeechRecognitionEvent) => void) | null
	onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
	onend: (() => void) | null
	onstart: (() => void) | null
}

declare global {
	interface Window {
		SpeechRecognition: new () => SpeechRecognition
		webkitSpeechRecognition: new () => SpeechRecognition
	}
}

interface UseSTTOptions {
	language?: string
	continuous?: boolean
	interimResults?: boolean
	onResult?: (transcript: string, isFinal: boolean) => void
	onError?: (error: string) => void
}

interface UseSTTReturn {
	isListening: boolean
	isSupported: boolean
	transcript: string
	startListening: () => void
	stopListening: () => void
	resetTranscript: () => void
}

/**
 * Hook for Speech-to-Text functionality using the Web Speech API.
 * Uses browser's native speech recognition (Chrome/Edge webkitSpeechRecognition).
 *
 * @param options Configuration options
 * @returns STT controls and state
 */
export function useSTT(options: UseSTTOptions = {}): UseSTTReturn {
	const {
		language = "fr-FR",
		continuous = false,
		interimResults = true,
		onResult,
		onError
	} = options

	const [isListening, setIsListening] = useState(false)
	const [transcript, setTranscript] = useState("")
	const recognitionRef = useRef<SpeechRecognition | null>(null)

	// Check if Speech Recognition is supported
	const isSupported = typeof window !== "undefined" && (
		"SpeechRecognition" in window ||
		"webkitSpeechRecognition" in window
	)

	// Initialize recognition instance
	useEffect(() => {
		if (!isSupported) return

		const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition
		const recognition = new SpeechRecognitionAPI()

		recognition.continuous = continuous
		recognition.interimResults = interimResults
		recognition.lang = language

		recognition.onstart = () => {
			setIsListening(true)
		}

		recognition.onresult = (event: SpeechRecognitionEvent) => {
			let finalTranscript = ""
			let interimTranscript = ""

			for (let i = event.resultIndex; i < event.results.length; i++) {
				const result = event.results[i]
				if (result.isFinal) {
					finalTranscript += result[0].transcript
				} else {
					interimTranscript += result[0].transcript
				}
			}

			const currentTranscript = finalTranscript || interimTranscript
			setTranscript(currentTranscript)

			if (onResult) {
				onResult(currentTranscript, !!finalTranscript)
			}
		}

		recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
			console.error("Speech recognition error:", event.error)
			setIsListening(false)

			if (onError) {
				onError(event.error)
			}
		}

		recognition.onend = () => {
			setIsListening(false)
		}

		recognitionRef.current = recognition

		return () => {
			if (recognitionRef.current) {
				recognitionRef.current.abort()
			}
		}
	}, [isSupported, language, continuous, interimResults, onResult, onError])

	const startListening = useCallback(() => {
		if (!isSupported || !recognitionRef.current) {
			console.error("Speech recognition is not supported in this browser")
			if (onError) {
				onError("not-supported")
			}
			return
		}

		// Reset transcript when starting new recording
		setTranscript("")

		try {
			recognitionRef.current.start()
		} catch (error) {
			// Recognition may already be running
			console.error("Error starting speech recognition:", error)
		}
	}, [isSupported, onError])

	const stopListening = useCallback(() => {
		if (recognitionRef.current) {
			recognitionRef.current.stop()
		}
	}, [])

	const resetTranscript = useCallback(() => {
		setTranscript("")
	}, [])

	return {
		isListening,
		isSupported,
		transcript,
		startListening,
		stopListening,
		resetTranscript
	}
}
