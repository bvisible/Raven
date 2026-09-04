import { DMChannelListItem } from '@raven/types/common/ChannelListItem';
//// Neoffice - DM sidebar rework (b8b8dd25c + 40efaffad, 2026-01-05 + b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list").
//// useContext/useMemo for the user list and the message preview below.
import { useContext, useMemo, useState } from 'react';
import { View, Pressable, StyleSheet, TouchableOpacity } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { useColorScheme } from '@hooks/useColorScheme';
import ChevronDownIcon from '@assets/icons/ChevronDownIcon.svg';
import ChevronRightIcon from '@assets/icons/ChevronRightIcon.svg';
import { useGetUser } from '@raven/lib/hooks/useGetUser';
import UserAvatar from '@components/layout/UserAvatar';
//// Neoffice - "all users" DM sidebar (b8b8dd25c + 40efaffad, 2026-01-05): router, to open the channel just created.
import { Link, router } from 'expo-router';
import { useIsUserActive } from '@hooks/useIsUserActive';
//// Neoffice - DM sidebar rework (b8b8dd25c + 40efaffad, 2026-01-05 "feat(mobile): Show extra users without DM in
//// sidebar" + b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"). Upstream's sidebar lists existing DM channels only
//// and shows just the name; ours also lists the first few colleagues with no DM yet and shows the
//// last message with its time.
import { useTranslation } from 'react-i18next';
import { UserListContext } from '@raven/lib/providers/UserListProvider';
import { ChannelListContext, ChannelListContextType } from '@raven/lib/providers/ChannelListProvider';
import { useFrappePostCall } from 'frappe-react-sdk';
import { toast } from 'sonner-native';
import { UserFields } from '@raven/types/common/UserFields';
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser';
import dayjs from 'dayjs';

const DMList = ({ dms }: { dms: DMChannelListItem[] }) => {
    return <DMListUI dms={dms} />
}

//// Neoffice - DMListRow moved above DMListUI (6ccf2be7c, 2026-01-05 "fix(mobile): Reorder
//// components to fix hoisting issue") and gains t for the relative timestamps below. The hunks
//// down to L100 are that move plus the message-preview block, not a rewrite of the row.
export const DMListRow = ({ dm }: { dm: DMChannelListItem }) => {
    const { t } = useTranslation()
    const user = useGetUser(dm.peer_user_id)
    const isActive = useIsUserActive(dm.peer_user_id)

    //// Neoffice - last-message preview (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"): last_message_details arrives as a JSON
    //// string; a malformed payload must render an empty preview, never throw in the list.
    // Parse last message details
    const lastMessageContent = useMemo(() => {
        if (dm.last_message_details) {
            try {
                const parsedDetails = JSON.parse(dm.last_message_details)
                return parsedDetails.content?.trim() || ''
            } catch (e) {
                return ''
            }
        }
        return ''
    }, [dm.last_message_details])

    //// Neoffice - last-message timestamp (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"): today -> HH:mm (24h, a4eb3b921, 2026-01-06 "fix: Use 24-hour time format instead of 12-hour AM/PM"),
    //// yesterday -> translated word, this week -> weekday, older -> date.
    // Format timestamp
    const formattedTime = useMemo(() => {
        if (!dm.last_message_timestamp) return ''
        const dateObj = dayjs(dm.last_message_timestamp)
        if (!dateObj.isValid()) return ''

        //// Neoffice - continuation of the DMListRow/DMListUI reorder (6ccf2be7c, 2026-01-05); the removed
        //// lines reappear further down this file, they are not dropped.
        const today = dayjs()
        const yesterday = today.subtract(1, 'day')

        //// Neoffice - last-message timestamp (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"), continued.
        if (dateObj.isSame(today, 'day')) {
            return dateObj.format('HH:mm')
        }
        if (dateObj.isSame(yesterday, 'day')) {
            return t('common.yesterday')
        }
        if (dateObj.isSame(today, 'week')) {
            return dateObj.format('ddd')
        }
        return dateObj.format('D MMM')
    }, [dm.last_message_timestamp, t])

    return (
        <Link href={`../chat/${dm.name}`} asChild>
            <Pressable
                //// Neoffice - DM row made taller (py-1.5 -> py-2) to fit the two-line name + preview layout
                //// (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"). The two upstream comments go with the lines they described.
                className='flex-row items-center px-3 py-2 rounded-lg ios:active:bg-linkColor'
                android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}
            >
                <UserAvatar
                    src={user?.user_image ?? ""}
                    alt={user?.full_name ?? ""}
                    isActive={isActive}
                    availabilityStatus={user?.availability_status}
                    //// Neoffice - bigger avatar and name for the two-line row (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list").
                    avatarProps={{ className: "w-10 h-10" }}
                    textProps={{ className: "text-base font-medium" }}
                    isBot={user?.type === 'Bot'} />
                {/* //// Neoffice - two-line DM row (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"): name + time on the first line, message
                    //// preview on the second. Upstream renders the name alone. Name falls back to the user id
                    //// (fe1132079, 2026-01-04 "fix(mobile): add fallback for empty user full_name in DM displays"). */}
                <View className='flex-1 ml-3'>
                    <View className='flex-row justify-between items-center'>
                        <Text className='text-base font-medium' numberOfLines={1}>
                            {user?.full_name || user?.name || ''}
                        </Text>
                        {formattedTime ? (
                            <Text className='text-xs text-muted-foreground ml-2'>
                                {formattedTime}
                            </Text>
                        ) : null}
                    </View>
                    {lastMessageContent ? (
                        <Text className='text-sm text-muted-foreground' numberOfLines={1}>
                            {lastMessageContent}
                        </Text>
                    ) : null}
                </View>
            </Pressable>
        </Link>
    )
}

//// Neoffice - "extra users" sidebar section (b8b8dd25c + 40efaffad, 2026-01-05 "feat(mobile): Show extra users without
//// DM in sidebar") + self-DM filter (1400e92c5, 2026-01-05 "fix: Filter out self-DMs from DM lists"). Upstream's sidebar can only show
//// channels that already exist, so a colleague you never wrote to is unreachable from it: this
//// lists up to 5 of them and creates the channel on tap. TO REVIEW: the toast.error string here
//// is still hardcoded English - it escaped the i18n pass.
const ExtraUserItem = ({ user, createDMChannel }: { user: UserFields, createDMChannel: (user_id: string) => Promise<void> }) => {
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
            className='flex-row items-center px-3 py-2 rounded-lg ios:active:bg-linkColor'
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
            <View className='flex-1 ml-3'>
                <Text className='text-base font-medium' numberOfLines={1}>
                    {user.full_name || user.name || ''}
                </Text>
            </View>
        </Pressable>
    )
}

const ExtraUsersItemList = ({ dms }: { dms: DMChannelListItem[] }) => {
    const { enabledUsers } = useContext(UserListContext)
    const { mutate } = useContext(ChannelListContext) as ChannelListContextType
    const { myProfile } = useCurrentRavenUser()

    const { call } = useFrappePostCall<{ message: string }>('raven.api.raven_channel.create_direct_message_channel')

    const createDMChannel = async (user_id: string) => {
        return call({ user_id })
            .then((r) => {
                router.push(`../chat/${r?.message}`)
                mutate()
            })
            .catch(() => {
                toast.error('Could not create channel')
            })
    }

    const filteredUsers = useMemo(() => {
        // Show only users who are not in the DM list (excluding self)
        return Array.from(enabledUsers.values())
            .filter((user) => user.name !== myProfile?.name) // Exclude self
            .filter((user) => !dms.find((channel) => channel.peer_user_id === user.name))
            .slice(0, 5)
    }, [enabledUsers, dms, myProfile?.name])

    return (
        <>
            {filteredUsers.map((user) => (
                <ExtraUserItem key={user.name} user={user} createDMChannel={createDMChannel} />
            ))}
        </>
    )
}

const DMListUI = ({ dms }: { dms: DMChannelListItem[] }) => {
    const { t } = useTranslation();
    const [isExpanded, setIsExpanded] = useState(true)
    const { colors } = useColorScheme()
    const { myProfile } = useCurrentRavenUser()

    const toggleAccordion = () => {
        setIsExpanded((prev) => !prev)
    }

    // Filter out self-DMs (DMs with yourself)
    const filteredDMs = useMemo(() => {
        return dms.filter(dm => dm.peer_user_id !== myProfile?.name)
    }, [dms, myProfile?.name])

    return (
        <View style={styles.container}>
            <TouchableOpacity onPress={toggleAccordion} style={styles.header} activeOpacity={0.7}>
                <Text style={styles.headerText}>{t('channels.directMessages')}</Text>
                {isExpanded ? <ChevronDownIcon fill={colors.icon} /> : <ChevronRightIcon fill={colors.icon} />}
            </TouchableOpacity>
            {isExpanded && <>
                {filteredDMs.map((dm) => <DMListRow key={dm.name} dm={dm} />)}
                {filteredDMs.length < 5 && <ExtraUsersItemList dms={filteredDMs} />}
            </>}
        </View>
    )
}

const styles = StyleSheet.create({
    container: {
        padding: 10,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 12,
        paddingHorizontal: 10,
    },
    headerText: {
        fontWeight: '600',
        fontSize: 16,
    },
//// Neoffice - the dmChannelText style went away with the two-line row above (b02d80832, 2026-01-07 "feat: Show last message preview and time in DM list"),
//// which uses Tailwind classes instead of the StyleSheet entry.
})

//// Neoffice - newline at end of file added by the same commit. No code change.
export default DMList
