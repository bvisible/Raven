import { useColorScheme } from '@hooks/useColorScheme';
import { Pressable, View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { ChannelIcon } from '@components/features/channels/ChannelList/ChannelIcon';
import { ChannelListItem } from '@raven/types/common/ChannelListItem';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

interface ChannelRowItemProps {
    channel: ChannelListItem
    onPress?: (channel: ChannelListItem) => void
}

const ChannelRowItem = ({ channel, onPress }: ChannelRowItemProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    return (
        <Pressable
            onPress={() => onPress?.(channel)}
            className='flex flex-row gap-2 items-center px-2 py-2 rounded-lg ios:active:bg-linkColor'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <ChannelIcon type={channel.type} fill={colors.icon} />
            <Text className="text-base">{channel.channel_name}</Text>
            {channel.is_archived ? (
                <View className='px-1 mt-0.5 py-0.5 rounded-sm bg-red-100'>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className="text-[11px] text-red-700">{t('common.archived')}</Text>
                </View>
            ) : null}
        </Pressable>
    )
}

export default ChannelRowItem