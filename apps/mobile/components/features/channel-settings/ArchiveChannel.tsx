import { ChannelListContext, ChannelListContextType } from '@raven/lib/providers/ChannelListProvider'
import { ChannelListItem } from '@raven/types/common/ChannelListItem'
import { FrappeDoc, useFrappeUpdateDoc } from 'frappe-react-sdk'
import { useContext } from 'react'
import { Alert, Pressable } from 'react-native'
import { toast } from 'sonner-native'
import { Text } from '@components/nativewindui/Text'
import ArchiveIcon from "@assets/icons/ArchiveIcon.svg";
import { useColorScheme } from '@hooks/useColorScheme'
import { useRouteToHome } from '@hooks/useRouting'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const ArchiveChannel = ({ channel }: { channel: FrappeDoc<ChannelListItem> | undefined }) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { updateDoc, loading, error } = useFrappeUpdateDoc()
    const { mutate } = useContext(ChannelListContext) as ChannelListContextType

    const { colors } = useColorScheme()

    const goToHome = useRouteToHome()

    const onArchiveChannel = () => {
        updateDoc('Raven Channel', channel?.name ?? '', {
            is_archived: 1
        }).then(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('channels.channelArchived'))
            goToHome()
            mutate()
        }).catch(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('channels.archiveChannelFailed'), {
                description: error?.httpStatusText
            })
        })
    };

    const onArchiveChannelPressed = () => {
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        Alert.alert(t('channels.archiveChannelConfirm'), t('channels.archiveChannelMessage', { channelName: channel?.channel_name }), [
            { text: t('common.cancel'), style: 'cancel' },
            { text: t('common.archive'), style: 'destructive', onPress: onArchiveChannel },
        ])
    }

    return (
        <Pressable
            onPress={onArchiveChannelPressed}
            className='flex flex-row items-center py-3 px-4 rounded-xl gap-3 bg-background dark:bg-card active:bg-card-background/50 dark:active:bg-card/80'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <ArchiveIcon height={18} width={18} fill={colors.icon} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="text-base">{loading ? t('channels.archiving') : t('channels.archiveChannel')}</Text>
        </Pressable>
    )
}

export default ArchiveChannel