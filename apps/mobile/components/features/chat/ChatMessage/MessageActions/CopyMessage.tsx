import * as Clipboard from 'expo-clipboard'
import { Message } from '@raven/types/common/Message'
import { toast } from 'sonner-native'
import { useColorScheme } from '@hooks/useColorScheme'
import CopyIcon from "@assets/icons/CopyIcon.svg"
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface CopyMessageProps {
    message: Message
    onClose: () => void
}

const CopyMessage = ({ message, onClose }: CopyMessageProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const copy = useMessageCopy(message)

    return (
        <ActionButton
            onPress={() => copy(onClose)}
            icon={<CopyIcon width={18} height={18} fill={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.copy')}
        />
    )
}

export default CopyMessage

//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useMessageCopy is called from a plain action factory as
//// well as from a component, so t comes in as an optional argument rather than from a hook.
export const useMessageCopy = (message: Message, t?: (key: string) => string) => {

    const copy = async (onSuccess: () => void) => {
        if (!message) return

        if (message.message_type === 'Text') {
            // Remove all empty lines
            let text = message.text.replace(/^\s*[\r\n]/gm, "")

            // Simple HTML to plain text conversion
            const plainText = text.replace(/<[^>]+>/g, '')

            if (plainText) {
                await Clipboard.setStringAsync(plainText)
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t ? t('messages.textCopied') : 'Text copied to clipboard')
                onSuccess()
            } else {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t ? t('messages.copyFailed') : 'Could not copy text')
            }

        }
    }

    return copy
}