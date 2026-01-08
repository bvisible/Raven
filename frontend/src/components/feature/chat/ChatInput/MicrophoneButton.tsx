import { useSTT } from "@/hooks/useSTT"
import { __ } from "@/utils/translations"
import { IconButton, Tooltip } from "@radix-ui/themes"
import { useCurrentEditor } from "@tiptap/react"
import { useCallback, useEffect } from "react"
import { BiMicrophone, BiMicrophoneOff } from "react-icons/bi"
import { toast } from "sonner"
import { DEFAULT_BUTTON_STYLE, ICON_PROPS } from "./ToolPanel"

interface MicrophoneButtonProps {
	/** Language for speech recognition (default: fr-FR) */
	language?: string
}

/**
 * Microphone button for voice dictation using Web Speech API.
 * Inserts transcribed text into the Tiptap editor.
 */
export const MicrophoneButton = ({ language = "fr-FR" }: MicrophoneButtonProps) => {
	const { editor } = useCurrentEditor()

	const handleResult = useCallback((transcript: string, isFinal: boolean) => {
		if (editor && isFinal && transcript.trim()) {
			// Insert the transcribed text at the cursor position
			editor.chain().focus().insertContent(transcript + " ").run()
		}
	}, [editor])

	const handleError = useCallback((error: string) => {
		if (error === "not-allowed") {
			toast.error(__("Microphone access denied"), {
				description: __("Please allow microphone access in your browser settings")
			})
		} else if (error === "not-supported") {
			toast.error(__("Speech recognition not supported"), {
				description: __("Your browser does not support speech recognition")
			})
		} else if (error !== "no-speech" && error !== "aborted") {
			// Don't show error for no-speech or aborted (user stopped)
			toast.error(__("Speech recognition error"), {
				description: error
			})
		}
	}, [])

	const {
		isListening,
		isSupported,
		startListening,
		stopListening
	} = useSTT({
		language,
		continuous: true,
		interimResults: true,
		onResult: handleResult,
		onError: handleError
	})

	// Clean up when component unmounts
	useEffect(() => {
		return () => {
			if (isListening) {
				stopListening()
			}
		}
	}, [isListening, stopListening])

	if (!editor || !isSupported) {
		return null
	}

	const toggleListening = () => {
		if (isListening) {
			stopListening()
		} else {
			startListening()
		}
	}

	return (
		<Tooltip content={isListening ? __("Stop dictation") : __("Voice dictation")}>
			<IconButton
				size="1"
				variant="ghost"
				className={isListening
					? "bg-red-3 text-red-11 animate-pulse"
					: DEFAULT_BUTTON_STYLE
				}
				onClick={toggleListening}
				disabled={!editor.isEditable}
				title={isListening ? __("Stop dictation") : __("Voice dictation")}
				aria-label={isListening ? "stop dictation" : "start dictation"}
			>
				{isListening ? (
					<BiMicrophoneOff {...ICON_PROPS} className="text-red-11" />
				) : (
					<BiMicrophone {...ICON_PROPS} />
				)}
			</IconButton>
		</Tooltip>
	)
}

export default MicrophoneButton
