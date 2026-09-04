import { useColorScheme } from '@hooks/useColorScheme'
import { FileMessage } from '@raven/types/common/Message'
import PaperClipIcon from "@assets/icons/PaperClipIcon.svg"
import { toast } from 'sonner-native'
import * as Clipboard from 'expo-clipboard'
import useSiteContext from '@hooks/useSiteContext'
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface CopyFileMessageLinkProps {
    message: FileMessage
    onClose: () => void
}

const CopyFileMessageLink = ({ message, onClose }: CopyFileMessageLinkProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const siteData = useSiteContext()

    const copyLink = () => {
        if (message.file.startsWith('http') || message.file.startsWith('https')) {
            Clipboard.setStringAsync(message.file)
        }
        else {
            Clipboard.setStringAsync(siteData?.url + message.file.split('?')[0])
        }
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        toast.success(t('messages.linkCopied'))
        onClose()
    }

    return (
        <ActionButton
            onPress={copyLink}
            icon={<PaperClipIcon width={18} height={18} fill={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('media.copyFileLink')}
        />
    )
}

export default CopyFileMessageLink