import { DMChannelListItem } from '@raven/types/common/ChannelListItem';
import { useContext, useMemo, useState } from 'react';
import { View, Pressable, StyleSheet, TouchableOpacity } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { useColorScheme } from '@hooks/useColorScheme';
import ChevronDownIcon from '@assets/icons/ChevronDownIcon.svg';
import ChevronRightIcon from '@assets/icons/ChevronRightIcon.svg';
import { useGetUser } from '@raven/lib/hooks/useGetUser';
import UserAvatar from '@components/layout/UserAvatar';
import { Link, router } from 'expo-router';
import { useIsUserActive } from '@hooks/useIsUserActive';
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

export const DMListRow = ({ dm }: { dm: DMChannelListItem }) => {
    const { t } = useTranslation()
    const user = useGetUser(dm.peer_user_id)
    const isActive = useIsUserActive(dm.peer_user_id)

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

    // Format timestamp
    const formattedTime = useMemo(() => {
        if (!dm.last_message_timestamp) return ''
        const dateObj = dayjs(dm.last_message_timestamp)
        if (!dateObj.isValid()) return ''

        const today = dayjs()
        const yesterday = today.subtract(1, 'day')

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
                className='flex-row items-center px-3 py-2 rounded-lg ios:active:bg-linkColor'
                android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}
            >
                <UserAvatar
                    src={user?.user_image ?? ""}
                    alt={user?.full_name ?? ""}
                    isActive={isActive}
                    availabilityStatus={user?.availability_status}
                    avatarProps={{ className: "w-10 h-10" }}
                    textProps={{ className: "text-base font-medium" }}
                    isBot={user?.type === 'Bot'} />
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
})

export default DMList
