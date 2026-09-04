import { Text } from '@components/nativewindui/Text';
import { FrappeDoc, useFrappePostCall } from 'frappe-react-sdk';
import { useContext } from 'react';
import { ChannelListContext, ChannelListContextType } from '@raven/lib/providers/ChannelListProvider';
import { toast } from 'sonner-native';
import { ChannelListItem } from '@raven/types/common/ChannelListItem';
import { Alert, Pressable } from 'react-native';
import LeaveIcon from "@assets/icons/LeaveIcon.svg";
import { useColorScheme } from '@hooks/useColorScheme';
import { useRouteToHome } from '@hooks/useRouting';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const LeaveChannel = ({ channel }: { channel: FrappeDoc<ChannelListItem> | undefined }) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call, error } = useFrappePostCall("raven.api.raven_channel.leave_channel")
    const { mutate } = useContext(ChannelListContext) as ChannelListContextType

    const { colors } = useColorScheme()

    const goToHome = useRouteToHome()

    const onLeaveChannel = async () => {
        return call({ channel_id: channel?.name })
            .then(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('channels.leftChannel', { channelName: channel?.channel_name }))
                goToHome()
                mutate()
            })
            .catch(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('channels.leaveChannelFailed'), {
                    description: error?.httpStatusText
                })
            })
    }

    const onLeaveChannelPressed = () => {
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        Alert.alert(t('channels.leaveChannelConfirm'), t('channels.leaveChannelMessage', { channelName: channel?.channel_name }), [
            { text: t('common.cancel'), style: 'cancel' },
            { text: t('common.leave'), style: 'destructive', onPress: onLeaveChannel },
        ])
    }

    return (
        <Pressable
            onPress={onLeaveChannelPressed}
            className='flex flex-row items-center py-3 px-4 rounded-xl gap-3 bg-background dark:bg-card ios:active:bg-red-50 dark:ios:active:bg-red-100/10'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <LeaveIcon height={18} width={18} fill={colors.destructive} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="text-base text-destructive">{t('channels.leaveChannel')}</Text>
        </Pressable>
    )
}

export default LeaveChannel