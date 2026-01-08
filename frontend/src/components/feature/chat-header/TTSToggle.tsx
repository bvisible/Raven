import { useTTS } from "@/hooks/useTTS"
import { __ } from "@/utils/translations"
import { Flex, Switch, Text, Tooltip, IconButton } from "@radix-ui/themes"
import { HiSpeakerWave, HiSpeakerXMark } from "react-icons/hi2"

interface TTSToggleProps {
	/** Compact mode shows only icon and switch */
	compact?: boolean
}

/**
 * Toggle switch for Text-to-Speech auto-read functionality.
 * When enabled, AI bot messages will be automatically read aloud.
 */
export const TTSToggle = ({ compact = false }: TTSToggleProps) => {
	const { ttsEnabled, setTTSEnabled, isPlaying, stop } = useTTS()

	const handleToggle = (checked: boolean) => {
		setTTSEnabled(checked)
		// If disabling while playing, stop the audio
		if (!checked && isPlaying) {
			stop()
		}
	}

	if (compact) {
		return (
			<Flex align="center" gap="2">
				<Tooltip content={ttsEnabled ? __("Disable TTS") : __("Enable TTS")}>
					<Flex align="center" gap="1">
						{ttsEnabled ? (
							<HiSpeakerWave size="14" className="text-gray-11" />
						) : (
							<HiSpeakerXMark size="14" className="text-gray-11" />
						)}
						<Switch
							size="1"
							checked={ttsEnabled}
							onCheckedChange={handleToggle}
						/>
					</Flex>
				</Tooltip>
				{isPlaying && (
					<Tooltip content={__("Stop audio")}>
						<IconButton
							size="1"
							variant="ghost"
							color="red"
							onClick={stop}
						>
							<HiSpeakerXMark size="14" />
						</IconButton>
					</Tooltip>
				)}
			</Flex>
		)
	}

	return (
		<Flex align="center" gap="2">
			<Tooltip content={__("Auto-read AI messages aloud")}>
				<Flex align="center" gap="2">
					{ttsEnabled ? (
						<HiSpeakerWave size="16" className="text-gray-11" />
					) : (
						<HiSpeakerXMark size="16" className="text-gray-11" />
					)}
					<Text as="label" size="2" color="gray">
						TTS
					</Text>
					<Switch
						size="1"
						checked={ttsEnabled}
						onCheckedChange={handleToggle}
					/>
				</Flex>
			</Tooltip>
			{isPlaying && (
				<Tooltip content={__("Stop audio")}>
					<IconButton
						size="1"
						variant="ghost"
						color="red"
						onClick={stop}
					>
						<HiSpeakerXMark size="14" />
					</IconButton>
				</Tooltip>
			)}
		</Flex>
	)
}

export default TTSToggle
