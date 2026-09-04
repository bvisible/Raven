import { Message } from "@raven/types/common/Message"
import { FrappeConfig, FrappeContext } from "frappe-react-sdk"
import { useContext, useState } from "react"
import { toast } from "sonner-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

export const useTogglePinMessage = (message: Message) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const isPinned = message.is_pinned
    const { call } = useContext(FrappeContext) as FrappeConfig
    const [error, setError] = useState<string | null>(null)
    const TogglePin = () => {
        call.post('raven.api.raven_channel.toggle_pin_message', {
            channel_id: message.channel_id,
            message_id: message.name,
        }).then(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(isPinned ? t('messages.messageUnpinned') : t('messages.messagePinned'))
        }).catch((e) => {
            console.error(e)
            setError(e)
        })
    }

    return { TogglePin, error }
}
