import { useColorScheme } from '@hooks/useColorScheme'
import { Message } from '@raven/types/common/Message'
import { router } from 'expo-router'
import ForwardIcon from "@assets/icons/ForwardIcon.svg"
import { ActionButtonLarge } from '@components/common/Buttons/ActionButtonLarge'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface ForwardMessageProps {
    message: Message
    onClose: () => void
}

const ForwardMessage = ({ message, onClose }: ForwardMessageProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()

    const forwardMessage = () => {
        router.push({
            pathname: "./forward-message",
            params: { ...message } as any
        }, { relativeToDirectory: true })
        onClose()
    }

    const { colors } = useColorScheme()

    return (
        <ActionButtonLarge
            icon={<ForwardIcon width={18} height={18} color={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.forward')}
            onPress={forwardMessage}
        />
    )
}

export default ForwardMessage