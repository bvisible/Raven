import { Message } from '@raven/types/common/Message'
import { useColorScheme } from '@hooks/useColorScheme'
import { useFrappePostCall } from "frappe-react-sdk"
import { toast } from "sonner-native"
import MessageIcon from "@assets/icons/MessageIcon.svg"
import { router } from 'expo-router'
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface CreateThreadProps {
    message: Message
    onClose: () => void
}

const CreateThread = ({ message, onClose }: CreateThreadProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const { createThread } = useCreateThread(message)

    const onPress = () => {
        createThread()
            .then((thread) => {
                onClose()
                if (thread) {
                    router.push(`../thread/${thread.thread_id}`)
                }
            })
    }

    return (
        <ActionButton
            onPress={onPress}
            icon={<MessageIcon width={18} height={18} fill={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.createThread')}
        />
    )
}

export default CreateThread

const useCreateThread = (message: Message) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call, loading } = useFrappePostCall<{ message: { channel_id: string, thread_id: string } }>("raven.api.threads.create_thread")

    const handleCreateThread = () => {
        return call({ message_id: message?.name })
            .then((res) => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('messages.threadCreated'))

                return res.message
            })
            .catch((error) => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('messages.threadCreationFailed'))
            })
    }

    return {
        createThread: handleCreateThread,
        loading
    }
}
