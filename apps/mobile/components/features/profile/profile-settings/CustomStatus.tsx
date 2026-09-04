import { TouchableOpacity, View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import SmileIcon from '@assets/icons/SmileIcon.svg'
import { useColorScheme } from '@hooks/useColorScheme'
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser'
import { router } from 'expo-router'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const CustomStatus = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const { myProfile } = useCurrentRavenUser()

    const handleGoToCustomStatus = () => {
        router.push('./custom-status', {
            relativeToDirectory: true
        })
    }

    return (
        <View>
            <View className='flex flex-row py-2.5 px-4 rounded-xl justify-between bg-background dark:bg-card'>
                <View className='flex-row items-center gap-2'>
                    <SmileIcon height={18} width={18} fill={colors.icon} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base'>{t('common.status')}</Text>
                </View>
                <TouchableOpacity onPress={handleGoToCustomStatus}>
                    {myProfile?.custom_status ? <Text className='text-base text-muted-foreground' numberOfLines={1}
                        ellipsizeMode="tail" // Add ellipsis at the end
                        style={{ maxWidth: 200 }} >
                        {myProfile?.custom_status}
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    </Text> : <Text className='text-base font-medium text-primary'>{t('common.add')}</Text>}
                </TouchableOpacity>
            </View>
        </View>
    )
}

export default CustomStatus