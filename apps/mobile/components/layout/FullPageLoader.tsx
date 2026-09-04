import { Text } from '@components/nativewindui/Text'
import { View } from 'react-native'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

type Props = {
    title?: string
    description?: string
}

//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): upstream puts the English defaults in the parameter
//// list, where t() cannot run yet (hooks may not be called before the component body). Defaults
//// are resolved inside the body instead. 'raven' also becomes the translated app name.
const FullPageLoader = ({ title, description }: Props) => {
    const { t } = useTranslation()
    const displayTitle = title ?? t('common.appName')
    const displayDescription = description ?? t('workspaces.settingUp')

    return (
        <View className="flex-1 bg-background justify-center items-center gap-2">
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): render the resolved values computed above. */}
            <Text className="text-4xl text-foreground font-cal-sans">{displayTitle}</Text>
            <Text className='text-muted-foreground'>{displayDescription}</Text>
        </View>
    )
}

export default FullPageLoader