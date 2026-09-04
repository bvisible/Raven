import * as ContextMenu from 'zeego/context-menu';
import { Alert, Pressable } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { ChannelIcon } from './ChannelIcon';
import { Text } from '@components/nativewindui/Text';
import { useColorScheme } from '@hooks/useColorScheme';
import { ChannelListItem } from '@raven/types/common/ChannelListItem';
import { Link } from 'expo-router';
import { ChannelListContext, ChannelListContextType } from '@raven/lib/providers/ChannelListProvider';
import { FrappeConfig, FrappeContext, useFrappePostCall } from 'frappe-react-sdk';
import { useContext, useMemo } from 'react';
import { toast } from 'sonner-native';
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser';
import { RavenUser } from '@raven/types/Raven/RavenUser';
import useSiteContext from '@hooks/useSiteContext';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export function ChannelListRow({ channel }: { channel: ChannelListItem }) {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    // const handleMuteChannel = () => {
    //     console.log(`Muting channel: ${channel.name}`)
    // }

    const { onMoveToStarred, isStarred } = useMoveToStarred(channel)

    const siteInfo = useSiteContext()
    const siteID = siteInfo?.url

    const handleCopyLink = async () => {
        try {
            const workspace = channel.workspace ?? 'channels'
            const link = `${siteID}/raven/${encodeURIComponent(workspace)}/${encodeURIComponent(channel.name)}`
            await Clipboard.setStringAsync(link)
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('messages.linkCopied'))
        } catch (error) {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('messages.copyFailed'))
        }
    }

    const { onLeaveChannel } = useLeaveChannel(channel)

    const showAlert = () =>
        Alert.alert(
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            t('channels.leaveChannelConfirm'),
            t('channels.leaveChannelMessage', { channelName: channel.channel_name }),
            [
                {
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text: t('common.cancel'),
                    style: 'cancel',
                },
                {
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text: t('common.leave'),
                    style: 'destructive',
                    onPress: onLeaveChannel
                },
            ]
        )

    return (
        <ContextMenu.Root>
            <ContextMenu.Trigger>
                <Link href={`../chat/${channel.name}`} asChild>
                    <Pressable
                        // long press -> this is a workaround to prevent a press to register on long press (esp on Android)
                        // Ref: https://github.com/nandorojo/zeego/issues/145
                        onLongPress={() => { }}
                        // Use tailwind classes for layout and ios:active state
                        className='flex-row items-center px-3 py-2 rounded-lg ios:active:bg-linkColor'
                        // Add a subtle ripple effect on Android
                        android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}
                    >
                        <ChannelIcon type={channel.type} fill={colors.icon} />
                        <Text className="ml-2 text-base">{channel.channel_name}</Text>
                    </Pressable>
                </Link>
            </ContextMenu.Trigger>

            <ContextMenu.Content>
                {/* <ContextMenu.Item key="mute" onSelect={handleMuteChannel}>
                    <ContextMenu.ItemTitle>Mute channel</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: 'bell.slash',
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
                </ContextMenu.Item> */}

                <ContextMenu.Item key="star" onSelect={onMoveToStarred}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <ContextMenu.ItemTitle>{isStarred ? t('channels.removeFromStarred') : t('channels.moveToStarred')}</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: isStarred ? 'star.fill' : 'star',
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

                <ContextMenu.Item key="copy" onSelect={handleCopyLink}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <ContextMenu.ItemTitle>{t('messages.copyLink')}</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: 'link',
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

                {channel.member_id && <ContextMenu.Item key="leave" destructive onSelect={showAlert}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <ContextMenu.ItemTitle>{t('channels.leaveChannel')}</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: 'rectangle.portrait.and.arrow.right',
                            pointSize: 12,
                            weight: 'semibold',
                            scale: 'medium',
                            // can also be a color string. Requires iOS 15+
                            hierarchicalColor: {
                                dark: 'red',
                                light: 'red',
                            },
                            // alternative to hierarchical color. Requires iOS 15+
                            paletteColors: [
                                {
                                    dark: 'red',
                                    light: 'red',
                                },
                            ],
                        }}
                    />
                </ContextMenu.Item>}

                <ContextMenu.Arrow />
            </ContextMenu.Content>
        </ContextMenu.Root>
    )
}

const useLeaveChannel = (channel: ChannelListItem) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call, error } = useFrappePostCall("raven.api.raven_channel.leave_channel")
    const { mutate } = useContext(ChannelListContext) as ChannelListContextType

    const onLeaveChannel = async () => {
        return call({ channel_id: channel?.name })
            .then(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('channels.leftChannel', { channelName: channel.channel_name }))
                mutate()
            })
            .catch(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('channels.leaveChannelFailed'), {
                    description: error?.httpStatusText
                })
            })
    }

    return { onLeaveChannel }
}

const useMoveToStarred = (channel: ChannelListItem) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { myProfile, mutate } = useCurrentRavenUser()

    const isStarred = useMemo(() => {
        if (myProfile) {
            return myProfile.pinned_channels?.map(pin => pin.channel_id).includes(channel.name)
        } else {
            return false
        }
    }, [channel.name, myProfile])

    const { call } = useContext(FrappeContext) as FrappeConfig

    const onMoveToStarred = async () => {
        call.post('raven.api.raven_channel.toggle_pinned_channel', {
            channel_id: channel.name
        }).then((res: { message: RavenUser }) => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(isStarred ? t('channels.removedFromFavorites', { channelName: channel.channel_name }) : t('channels.addedToFavorites', { channelName: channel.channel_name }))
            if (res.message) {
                mutate({ message: res.message }, { revalidate: false })
            }
        })
    }

    return { onMoveToStarred, isStarred }
}