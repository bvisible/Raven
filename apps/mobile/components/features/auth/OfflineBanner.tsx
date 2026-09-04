import { Text } from '@components/nativewindui/Text'
import { View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

type Props = {}

const OfflineBanner = (props: Props) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    return (
        <SafeAreaView edges={['top', 'left', 'right']} className='bg-card-foreground py-2'>
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-sm text-center text-background'>{t('auth.offlineMessage')}</Text>
        </SafeAreaView>
    )
}

export default OfflineBanner