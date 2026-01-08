import { atomWithStorage } from "jotai/utils"

export const EnterKeyBehaviourAtom = atomWithStorage<"new-line" | "send-message">("raven-enter-key-behaviour", "send-message", undefined, { getOnInit: true })

export const QuickEmojisAtom = atomWithStorage<string[]>("raven-quick-emojis", ["👍", "✅", "👀", "🎉"])

// TTS (Text-to-Speech) preference for AI bot conversations
export const TTSEnabledAtom = atomWithStorage<boolean>("raven-tts-enabled", false, undefined, { getOnInit: true })