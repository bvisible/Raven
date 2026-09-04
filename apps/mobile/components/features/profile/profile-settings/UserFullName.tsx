import { TouchableOpacity, View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser'
import { useColorScheme } from '@hooks/useColorScheme'
import UserIcon from '@assets/icons/UserIcon.svg'
import { router } from 'expo-router'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const UserFullName = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { myProfile } = useCurrentRavenUser()
    const { colors } = useColorScheme()

    const handleGoToFullNameUpdate = () => {
        router.push('./fullname', {
            relativeToDirectory: true
        })
    }

    return (
        <View>
            <View className='flex flex-row py-2.5 px-4 rounded-xl items-center justify-between bg-background dark:bg-card'>
                <View className='flex-row items-center gap-2'>
                    <UserIcon height={18} width={18} fill={colors.icon} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base'>{t('common.name')}</Text>
                </View>
                <TouchableOpacity onPress={handleGoToFullNameUpdate}>
                    <Text className='text-base text-foreground'>{myProfile?.full_name}</Text>
                </TouchableOpacity>
            </View>
        </View>
    )
}

export default UserFullName