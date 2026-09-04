import { atomWithStorage } from "jotai/utils"

export const EnterKeyBehaviourAtom = atomWithStorage<"new-line" | "send-message">("raven-enter-key-behaviour", "send-message", undefined, { getOnInit: true })

//// Neoffice - TTS preferences (98fb5650e, 2026-01-08 "feat(ai): add TTS/STT support for AI bot conversations" + 5332dcfb4, 2026-01-08 "fix: add voice
//// parameter to TTS API calls"). Per-browser, off by default. The default voice is Swiss French
//// because that is the customer base; getOnInit reads localStorage before the first render so
//// the toggle does not flip visibly on load.
export const QuickEmojisAtom = atomWithStorage<string[]>("raven-quick-emojis", ["👍", "✅", "👀", "🎉"])

// TTS (Text-to-Speech) preference for AI bot conversations
export const TTSEnabledAtom = atomWithStorage<boolean>("raven-tts-enabled", false, undefined, { getOnInit: true })

// TTS Voice preference - default to French Swiss male voice
export const TTSVoiceAtom = atomWithStorage<string>("raven-tts-voice", "fr-CH-FabriceNeural", undefined, { getOnInit: true })