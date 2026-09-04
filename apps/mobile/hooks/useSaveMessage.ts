import { Message } from "@raven/types/common/Message"
import { FrappeContext, FrappeConfig } from "frappe-react-sdk"
import { useContext, useState, useCallback } from "react"
import { toast } from "sonner-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

const useSaveMessage = (message: Message, user?: string, saved = true) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call } = useContext(FrappeContext) as FrappeConfig

    const [isSaved, setIsSaved] = useState(user ? JSON.parse(message?._liked_by ? message?._liked_by : '[]').includes(user) : saved)
    const [isLoading, setIsLoading] = useState(false)

    const save = useCallback(() => {
        if (!message) return

        setIsLoading(true)

        call.post('raven.api.raven_message.save_message', {
            message_id: message?.name,
            add: isSaved ? 'No' : 'Yes'
        }).then((response) => {

            if (!response?.message) return

            if (isSaved) {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast(t('messages.messageUnsaved'))
            } else {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('messages.messageSaved'))
            }

            setIsSaved(!isSaved)

        }).catch((e: unknown) => {
            console.error(e)
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('messages.saveMessageFailed'))
        }).finally(() => {
            setIsLoading(false)
        })
    }, [call, message, isSaved])

    return { save, isSaved, isLoading }
}

export default useSaveMessage