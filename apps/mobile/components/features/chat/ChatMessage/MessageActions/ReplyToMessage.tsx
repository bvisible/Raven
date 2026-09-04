import { Message } from '@raven/types/common/Message'
import ReplyIcon from "@assets/icons/ReplyIcon.svg"
import { useColorScheme } from '@hooks/useColorScheme'
import { useSetAtom } from 'jotai'
import { selectedReplyMessageAtomFamily } from '@lib/ChatInputUtils'
import useSiteContext from '@hooks/useSiteContext'
import { ActionButtonLarge } from '@components/common/Buttons/ActionButtonLarge'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface ReplyToMessageProps {
    message: Message
    onClose: () => void
}

const ReplyToMessage = ({ message, onClose }: ReplyToMessageProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const siteInfo = useSiteContext()

    const setSelectedReplyMessage = useSetAtom(selectedReplyMessageAtomFamily(siteInfo?.sitename + message.channel_id))
    const onReplyToMessage = () => {
        setSelectedReplyMessage(message)
        onClose()
    }

    return (
        <ActionButtonLarge
            icon={<ReplyIcon width={18} height={18} color={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.reply')}
            onPress={onReplyToMessage}
        />
    )
}

export default ReplyToMessage