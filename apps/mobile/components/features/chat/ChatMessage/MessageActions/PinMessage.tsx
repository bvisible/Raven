import { Message } from "@raven/types/common/Message"
import { useColorScheme } from "@hooks/useColorScheme"
import { useTogglePinMessage } from "@hooks/useTogglePinMessage"
import PinOutlineIcon from "@assets/icons/PinOutlineIcon.svg"
import UnpinOutlineIcon from "@assets/icons/UnpinOutlineIcon.svg"
import ActionButton from "@components/common/Buttons/ActionButton"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface PinMessageProps {
    message: Message
    onClose: () => void
}

const PinMessage = ({ message, onClose }: PinMessageProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const { TogglePin } = useTogglePinMessage(message)

    const handlePin = () => {
        TogglePin()
        onClose()
    }

    return (
        <ActionButton
            onPress={handlePin}
            icon={message.is_pinned === 1 ? <UnpinOutlineIcon height={18} width={18} stroke={colors.icon} /> : <PinOutlineIcon height={18} width={18} stroke={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={message.is_pinned === 1 ? t('messages.unpin') : t('messages.pin')}
        />
    )
}

export default PinMessage