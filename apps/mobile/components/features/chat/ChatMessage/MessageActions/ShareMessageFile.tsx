import { useColorScheme } from '@hooks/useColorScheme'
import { FileMessage } from '@raven/types/common/Message'
import useFileShare from '@hooks/useFileShare'
import { toast } from 'sonner-native'
import ShareIcon from "@assets/icons/ShareIcon.svg"
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface DownloadMessageFileProps {
    message: FileMessage
    onClose: () => void
}

const ShareMessageFile = ({ message, onClose }: DownloadMessageFileProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const { shareFile } = useFileShare(message.file)

    const downloadFile = () => {
        shareFile()
            .then(() => {
                onClose()
            })
            .catch((error) => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('media.shareFileFailed'))
            })
    }

    return (
        <ActionButton
            icon={<ShareIcon width={18} height={18} color={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.share')}
            onPress={downloadFile}
        />
    )
}

export default ShareMessageFile