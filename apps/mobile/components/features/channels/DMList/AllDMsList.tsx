import { useColorScheme } from "@hooks/useColorScheme"
import useUnreadMessageCount from "@hooks/useUnreadMessageCount"
import { ChannelListContext, ChannelListContextType } from "@raven/lib/providers/ChannelListProvider"
//// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05 "feat(mobile): Show all users in Direct
//// Messages tab"): needs the current user to exclude self from the extra-users list.
import useCurrentRavenUser from "@raven/lib/hooks/useCurrentRavenUser"
import { useContext, useMemo, useState } from "react"
//// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05): Pressable for the extra-user rows.
import { View, ActivityIndicator, Pressable } from "react-native"
import DMRow from "./DMRow"
import ChatOutlineIcon from "@assets/icons/ChatOutlineIcon.svg"
import ErrorBanner from "@components/common/ErrorBanner"
import { Divider } from "@components/layout/Divider"
import SearchInput from "@components/common/SearchInput/SearchInput"
import { useDebounce } from "@raven/lib/hooks/useDebounce"
import { Text } from "@components/nativewindui/Text"
import { LegendList } from "@legendapp/list"
//// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05 "feat(mobile): Show all users in Direct Messages
//// tab"). Upstream lists only channels that already exist, so a new colleague is invisible until
//// someone writes to them first. ExtraUserRow renders the users with no DM yet and creates the
//// channel on tap (raven.api.raven_channel.create_direct_message_channel). DMListEmptyState also
//// moves above its call site here (6ccf2be7c, 2026-01-05 "Reorder components to fix hoisting
//// issue") and gets its strings translated.
import { useTranslation } from "react-i18next"
import { UserListContext } from "@raven/lib/providers/UserListProvider"
import { useFrappePostCall } from "frappe-react-sdk"
import { router } from "expo-router"
import { toast } from "sonner-native"
import UserAvatar from "@components/layout/UserAvatar"
import { useIsUserActive } from "@hooks/useIsUserActive"
import { UserFields } from "@raven/types/common/UserFields"

const ExtraUserRow = ({ user, createDMChannel }: { user: UserFields, createDMChannel: (user_id: string) => Promise<void> }) => {
    const [isLoading, setIsLoading] = useState(false)
    const isActive = useIsUserActive(user.name)

    const onPress = () => {
        setIsLoading(true)
        createDMChannel(user.name).finally(() => setIsLoading(false))
    }

    return (
        <Pressable
            onPress={onPress}
            disabled={isLoading}
            className="flex-row items-center px-4 py-3 bg-background ios:active:bg-linkColor"
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}
            style={{ opacity: isLoading ? 0.5 : 1 }}
        >
            <UserAvatar
                src={user.user_image ?? ""}
                alt={user.full_name ?? ""}
                isActive={isActive}
                availabilityStatus={user.availability_status}
                avatarProps={{ className: "w-10 h-10" }}
                textProps={{ className: "text-base font-medium" }}
                isBot={user.type === 'Bot'}
            />
            <View className="ml-3 flex-1">
                <Text className="text-base font-medium">{user.full_name || user.name || ''}</Text>
            </View>
        </Pressable>
    )
}

const DMListEmptyState = ({ searchQuery }: { searchQuery?: string }) => {
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    return (
        <View className="flex flex-col gap-2 bg-background px-4 py-1">
            <View className="flex flex-row items-center gap-2">
                <ChatOutlineIcon fill={colors.icon} height={20} width={20} />
                <Text className="text-foreground text-base font-medium">
                    {searchQuery ? t('directMessages.noDMsFoundWithQuery', { query: searchQuery }) : t('directMessages.noDMsFound')}
                </Text>
            </View>
            <Text className="text-sm text-foreground/60">
                {searchQuery ? t('directMessages.tryDifferentSearch') : t('directMessages.startConversation')}
            </Text>
        </View>
    )
}

const AllDMsList = () => {

    //// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05): mutate to refresh the list after a channel is
    //// created, and the user list to compute who has no DM yet.
    const { t } = useTranslation()
    const { dm_channels, error, isLoading, mutate } = useContext(ChannelListContext) as ChannelListContextType
    const { enabledUsers } = useContext(UserListContext)
    const { unread_count } = useUnreadMessageCount()
    //// Neoffice - self-DM filter (1400e92c5, 2026-01-05 "fix: Filter out self-DMs from DM lists"): needs the current Raven User to compare against.
    const { myProfile } = useCurrentRavenUser()

    const allDMs = useMemo(() => {
        return dm_channels?.map(dm => ({
            ...dm,
            unread_count: unread_count?.message.find(item => item.name === dm.name)?.unread_count ?? 0
        })) ?? []
    }, [dm_channels, unread_count])

    const [searchQuery, setSearchQuery] = useState('')
    const debouncedSearchQuery = useDebounce(searchQuery, 250)
    const filteredDMs = useMemo(() => {
        return allDMs.filter(dm => {
            if (!dm.peer_user_id) return false
            //// Neoffice - self-DM filter (1400e92c5, 2026-01-05 "fix: Filter out self-DMs from DM lists"). Upstream lists the note-to-self channel among the
            //// DMs; on Neoffice instances that row was read as a duplicate of the user's own name.
            // Filter out self-DMs (DMs with yourself)
            if (dm.peer_user_id === myProfile?.name) return false
            return dm.peer_user_id?.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
        })
    //// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05): the users with no DM channel yet, filtered by
    //// the same search box, plus the call that creates the channel and routes to it.
    }, [allDMs, debouncedSearchQuery, myProfile?.name])

    // Get users without existing DM channels (excluding self)
    const extraUsers = useMemo(() => {
        return Array.from(enabledUsers.values())
            .filter((user) => user.name !== myProfile?.name) // Exclude self
            .filter((user) => !dm_channels.find((channel) => channel.peer_user_id === user.name))
            .filter((user) => {
                if (!debouncedSearchQuery) return true
                return user.full_name?.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
                    user.name?.toLowerCase().includes(debouncedSearchQuery.toLowerCase())
            })
    }, [enabledUsers, dm_channels, debouncedSearchQuery, myProfile?.name])

    const { call } = useFrappePostCall<{ message: string }>('raven.api.raven_channel.create_direct_message_channel')

    const createDMChannel = async (user_id: string) => {
        return call({ user_id })
            .then((r) => {
                router.push(`../chat/${r?.message}`)
                mutate()
            })
            .catch(() => {
                toast.error(t('directMessages.createDMFailed'))
            })
    }

    if (isLoading) {
        return <View className="flex-1 justify-center items-center h-full">
            <ActivityIndicator />
        </View>
    }

    if (error) {
        return (
            <ErrorBanner error={error} />
        )
    }

    return (
        <View className="flex flex-col">
            <View className="px-3 pt-3 pb-1.5">
                <SearchInput
                    onChangeText={setSearchQuery}
                    value={searchQuery}
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): search placeholder through t().
                    placeholder={t('common.search') + '...'}
                />
            </View>
            <View className='flex-1'>
                <LegendList
                    data={filteredDMs}
                    renderItem={({ item }) => {
                        return <DMRow dm={item} />
                    }}
                    keyExtractor={(item) => item.name}
                    estimatedItemSize={68}
                    ItemSeparatorComponent={() => <Divider />}
                    bounces={false}
                    showsVerticalScrollIndicator={false}
                    //// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05): the empty state must not show while the
                    //// extra-users section still has rows to offer.
                    ListEmptyComponent={filteredDMs.length === 0 && extraUsers.length === 0 ? <DMListEmptyState searchQuery={searchQuery} /> : null}
                />
                {/* //// Neoffice - "all users" DM tab (b8b8dd25c + 40efaffad, 2026-01-05): the extra-users section, below the real DMs. */}
                {extraUsers.length > 0 && (
                    <View>
                        {filteredDMs.length > 0 && <Divider prominent />}
                        {extraUsers.map((user) => (
                            <View key={user.name}>
                                <ExtraUserRow user={user} createDMChannel={createDMChannel} />
                                <Divider />
                            </View>
                        ))}
                    </View>
                )}
                <Divider prominent />
            </View>
        </View>
    )
}

//// Neoffice - DMListEmptyState moved to the top of this file (6ccf2be7c, 2026-01-05 "fix(mobile):
//// Reorder components to fix hoisting issue"); this is the tail of that move, not a deletion.
export default AllDMsList
