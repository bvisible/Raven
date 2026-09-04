import { Pressable, View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { Message } from '@raven/types/common/Message';
import { useMemo } from 'react';
import { DMChannelListItem } from '@raven/types/common/ChannelListItem';
import { useCurrentChannelData } from '@raven/lib/hooks/useCurrentChannelData';
import { useGetUserRecords } from '@raven/lib/hooks/useGetUserRecords';
import { formatDateAndTime } from '@raven/lib/utils/dateConversions';
import { BaseMessageItem } from '../chat-stream/BaseMessageItem';
import { useRouteToChannel } from '@hooks/useRouting';
import * as ContextMenu from 'zeego/context-menu';
import { useColorScheme } from '@hooks/useColorScheme';
import useSaveMessage from '@hooks/useSaveMessage';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const SavedMessageItem = ({ message }: { message: Message & { workspace?: string } }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { save } = useSaveMessage(message)

    const { colors } = useColorScheme()

    const { creation, channel_id } = message
    const users = useGetUserRecords()

    const { channel } = useCurrentChannelData(channel_id)
    const channelData = channel?.channelData

    const channelName = useMemo(() => {
        if (channelData) {
            if (channelData.is_direct_message) {
                const peer_user_name = users[(channelData as DMChannelListItem).peer_user_id]?.full_name ?? (channelData as DMChannelListItem).peer_user_id
                return `DM with ${peer_user_name}`
            } else {
                return channelData.channel_name
            }
        }
    }, [channelData])

    const goToChannel = useRouteToChannel()
    const handleNavigateToChannel = (channelID: string) => {
        goToChannel(channelID)
    }

    return (
        <ContextMenu.Root>
            <ContextMenu.Trigger>
                <Pressable
                    className='pb-2 rounded-md active:bg-linkColor active:dark:bg-linkColor'
                    onPress={() => handleNavigateToChannel(channel_id)}
                    // long press -> this is a workaround to prevent a press to register on long press (esp on Android)
                    // Ref: https://github.com/nandorojo/zeego/issues/145
                    onLongPress={() => { }}
                >
                    <View>
                        <View className='flex flex-row items-center px-3 pt-2 gap-2'>
                            <Text className='text-sm'>{channelName}</Text>
                            <Text className='text-[13px] text-muted'>|</Text>
                            <Text className='text-[13px] text-muted-foreground'>
                                {formatDateAndTime(creation)}
                            </Text>
                        </View>
                        <BaseMessageItem message={message} />
                    </View>
                </Pressable>
            </ContextMenu.Trigger>
            <ContextMenu.Content>
                <ContextMenu.Item key="unsave" onSelect={save}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <ContextMenu.ItemTitle>{t('messages.unsaveMessage')}</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: 'bookmark.slash',
                            pointSize: 14,
                            weight: 'semibold',
                            scale: 'medium',
                            // can also be a color string. Requires iOS 15+
                            hierarchicalColor: {
                                dark: colors.icon,
                                light: colors.icon,
                            },
                            // alternative to hierarchical color. Requires iOS 15+
                            paletteColors: [
                                {
                                    dark: colors.icon,
                                    light: colors.icon,
                                },
                            ],
                        }}
                    />
                </ContextMenu.Item>
            </ContextMenu.Content>
        </ContextMenu.Root>
    )
}

export default SavedMessageItem