import { Pressable, View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import SettingsIcon from '@assets/icons/SettingsIcon.svg'
import { useColorScheme } from '@hooks/useColorScheme'
import ChevronRightIconThin from '@assets/icons/ChevronRightIconThin.svg'
import { router } from 'expo-router'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const Preferences = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const handleGoToCustomStatus = () => {
        router.push('./preferences', {
            relativeToDirectory: true
        })
    }

    return (
        <Pressable onPress={handleGoToCustomStatus} className='bg-background dark:bg-card rounded-xl active:bg-card-background/50 dark:active:bg-card/80'>
            <View className='flex flex-row py-0 pl-4 pr-2 items-center justify-between'>
                <View className='flex-row items-center gap-2 py-2.5'>
                    <SettingsIcon height={18} width={18} color={colors.icon} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base'>{t('profile.preferences')}</Text>
                </View>
                <View className='flex-row h-10 items-center'>
                    <ChevronRightIconThin height={22} width={22} color={colors.grey} />
                </View>
            </View>
        </Pressable>
    )
}

export default Preferences