import { Message } from '@raven/types/common/Message'
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser'
import { useColorScheme } from '@hooks/useColorScheme'
import BookmarkIcon from "@assets/icons/BookmarkIcon.svg"
import BookmarkFilledIcon from "@assets/icons/BookmarkFilledIcon.svg"
import { ActionButtonLarge } from '@components/common/Buttons/ActionButtonLarge'
import useSaveMessage from '@hooks/useSaveMessage'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface SaveMessageProps {
    message: Message
    onClose: () => void
}

const SaveMessage = ({ message, onClose }: SaveMessageProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { myProfile } = useCurrentRavenUser()
    const { save, isSaved } = useSaveMessage(message, myProfile?.name)
    const { colors } = useColorScheme()

    const handleSaveMessage = () => {
        save()
        onClose()
    }

    return (
        <ActionButtonLarge
            icon={isSaved ? <BookmarkFilledIcon width={18} height={18} fill={colors.icon} /> : <BookmarkIcon width={18} height={18} fill={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={isSaved ? t('messages.unsave') : t('messages.save')}
            onPress={handleSaveMessage}
        />
    )
}

export default SaveMessage