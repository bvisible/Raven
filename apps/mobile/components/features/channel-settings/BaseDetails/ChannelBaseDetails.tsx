import { ChannelListItem } from '@raven/types/common/ChannelListItem'
import { FrappeDoc } from 'frappe-react-sdk'
import { View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import { ChannelIcon } from '@components/features/channels/ChannelList/ChannelIcon'
import { useColorScheme } from '@hooks/useColorScheme'
import { Button } from '@components/nativewindui/Button'
import { router } from 'expo-router'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const ChannelBaseDetails = ({ channelData }: { channelData: FrappeDoc<ChannelListItem> | undefined }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    return (
        <View className="flex-col pt-4 px-4 gap-2">
            <View className="flex-row justify-between items-center">
                <View className='flex-row items-center align-baseline gap-1'>
                    <ChannelIcon size={22} type={channelData?.type ?? 'Public'} fill={colors.foreground} />
                    <Text className='text-[20px] font-semibold'>{channelData?.channel_name}</Text>
                </View>
                <Button variant="plain" size="none"
                    onPress={() => { router.push(`../edit-channel-details`, { relativeToDirectory: true }) }}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-[15px] font-medium text-primary dark:text-secondary mr-1'>{t('common.edit')}</Text>
                </Button>
            </View>
            {channelData?.channel_description && <Text className='text-base font-normal text-muted-foreground'>{channelData?.channel_description}</Text>}
        </View >
    )
}

export default ChannelBaseDetails