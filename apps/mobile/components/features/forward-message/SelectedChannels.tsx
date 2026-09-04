import { View, TextInput, TouchableOpacity } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import UserAvatar from '@components/layout/UserAvatar'
import { ChannelIcon } from '@components/features/channels/ChannelList/ChannelIcon'
import { useColorScheme } from '@hooks/useColorScheme'
import { CombinedChannel } from './ForwardMessage'
import CrossIcon from '@assets/icons/CrossIcon.svg'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface SelectedChannelsProps {
    selectedChannels: CombinedChannel[]
    searchInput: string
    setSearchInput: (value: string) => void
    handleRemoveChannel: (channel: CombinedChannel) => void
    handleBackspace: () => void
}

export const SelectedChannels = ({ selectedChannels, searchInput, setSearchInput, handleRemoveChannel, handleBackspace }: SelectedChannelsProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    return (
        <View className={`flex-row items-center gap-2.5 px-3 py-3`}>
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="self-start text-base text-foreground">{t('forward.to')}</Text>
            <View className="flex-1 flex-row flex-wrap items-center gap-2 mr-5">
                {selectedChannels.map((channel: CombinedChannel) => {
                    const isDMChannel = channel.is_direct_message
                    const user = channel.user

                    if (isDMChannel && !user?.enabled) return null

                    return (
                        <TouchableOpacity
                            key={channel.name}
                            className="rounded-md h-7 pr-2.5 flex-row items-center gap-2.5 bg-linkColor/50 dark:bg-card-background"
                            onPress={() => handleRemoveChannel(channel)}
                            activeOpacity={0.7}>
                            {isDMChannel ? (
                                <UserAvatar
                                    src={user?.user_image ?? ""}
                                    alt={user?.full_name ?? ""}
                                    avatarProps={{ className: "w-7 h-full" }}
                                    textProps={{ className: 'text-xs' }}
                                    fallbackProps={{ className: "rounded-l-md rounded-r-none" }}
                                    imageProps={{ className: "rounded-l-full rounded-r-none" }}
                                />
                            ) : (
                                <View className="rounded-l-md h-full w-7 justify-center items-center bg-linkColor dark:bg-grayText/20">
                                    <ChannelIcon size={15} type={channel.type as string} fill={colors.icon} />
                                </View>
                            )}
                            <Text className="text-sm">
                                {isDMChannel
                                    //// Neoffice - DM name fallback (fe1132079, 2026-01-04 "fix(mobile): add fallback for empty user full_name in DM displays"): empty full_name rendered a blank chip.
                                    ? `${user?.full_name || user?.name || ''}`
                                    : channel.channel_name}
                            </Text>
                            <CrossIcon color={colors.icon} height={11} width={11} />
                        </TouchableOpacity>
                    )
                })}
                <TextInput
                    autoFocus
                    className="flex-1"
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    placeholder={selectedChannels.length === 0 ? t('forward.addChannelOrDM') : ""}
                    value={searchInput}
                    onChangeText={setSearchInput}
                    onKeyPress={({ nativeEvent }) => {
                        if (nativeEvent.key === "Backspace") handleBackspace()
                    }}
                />
            </View>
        </View>
    )
} 