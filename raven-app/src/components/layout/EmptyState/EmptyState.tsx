import { ChannelListItem, DMChannelListItem } from "@/utils/channel/ChannelListProvider"
import { useCurrentChannelData } from "@/hooks/useCurrentChannelData"
import { useContext } from "react"
import { ChannelMembers, ChannelMembersContext, ChannelMembersContextType } from "@/utils/channel/ChannelMembersProvider"
import { EditDescriptionButton } from "@/components/feature/channel-details/edit-channel-description/EditDescriptionButton"
import { AddMembersButton } from "@/components/feature/channel-member-details/add-members/AddMembersButton"
import { UserContext } from "@/utils/auth/UserProvider"
import { useGetUserRecords } from "@/hooks/useGetUserRecords"
import { Box, Flex, Heading, Link, Text } from "@radix-ui/themes"
import { UserAvatar } from "@/components/common/UserAvatar"
import { ChannelIcon } from "@/utils/layout/channelIcon"
import { BiBookmark } from "react-icons/bi"
import { DateMonthYear } from "@/utils/dateConversions"

export const EmptyStateForSearch = () => {
    return (
        <Flex justify="center" align="center" className={'w-full h-64'}>
            <Flex direction='column' gap='1' className="text-center">
                <Text weight="bold" size='5'>Nothing turned up</Text>
                <Text as='span' size='2'>You may want to try using different keywords, checking for typos or adjusting your filters.</Text>
                <Text as='span' size='2'>Not the results that you expected? File an issue on <Link href="https://github.com/The-Commit-Company/Raven" target="_blank" rel="noreferrer">
                    <Text color='blue' size='2'>GitHub</Text>
                </Link>.
                </Text>
            </Flex>
        </Flex>
    )
}

interface EmptyStateForChannelProps {
    channelData: ChannelListItem,
    channelMembers: ChannelMembers,
    updateMembers: () => void
}

const EmptyStateForChannel = ({ channelData, channelMembers, updateMembers }: EmptyStateForChannelProps) => {

    const { currentUser } = useContext(UserContext)
    const users = useGetUserRecords()

    return (
        <Flex direction='column' className={'py-4 px-2'} gap='2'>
            <Flex direction='column' gap='2'>
                <Flex align={'center'} gap='1'>
                    <ChannelIcon type={channelData?.type} />
                    <Heading size='4'>{channelData?.channel_name}</Heading>
                </Flex>
                <Text size='2'>{users[channelData.owner]?.full_name} a créé ce canal le <DateMonthYear date={channelData?.creation} />. Il s'agit du tout début du <strong>{channelData?.channel_name}</strong> canal.</Text>
                {channelData?.channel_description && <Text size={'1'} color='gray'>{channelData?.channel_description}</Text>}
            </Flex>
            {channelData?.is_archived == 0 && channelMembers[currentUser] && <Flex gap='4' className={'z-1'}>
                <EditDescriptionButton channelData={channelData} />
                {channelData?.type !== 'Open' && <AddMembersButton channelData={channelData} updateMembers={updateMembers} channelMembers={channelMembers} />}
            </Flex>}
        </Flex>
    )
}

interface EmptyStateForDMProps {
    channelData: DMChannelListItem
}

const EmptyStateForDM = ({ channelData }: EmptyStateForDMProps) => {

    const peer = channelData.peer_user_id
    const users = useGetUserRecords()

    return (
        <Box className={'py-4 px-2'}>
            {channelData?.is_direct_message == 1 &&
                <Flex direction='column' gap='2'>
                    <Flex gap='2'>
                        <UserAvatar alt={users?.[peer]?.full_name ?? peer} src={users?.[peer]?.user_image ?? ''} size='3' skeletonSize='7' />
                        <Flex direction='column' gap='0'>
                            <Heading size='4'>{users?.[peer]?.full_name}</Heading>
                            <Text size='1' color='gray'>{users?.[peer]?.name}</Text>
                        </Flex>
                    </Flex>
                    {channelData?.is_self_message == 1 ?
                        <Flex direction='column' gap='0'>
                            <Text size='2'><strong>Cet espace est à vous.</strong> Rédigez des messages, dressez la liste de vos tâches ou gardez des liens et des fichiers à portée de main. </Text>
                            <Text size='2'></Text>
                        </Flex>
                        :
                        <Flex gap='2' align='center'>
                            <Text size='2'>Il s'agit d'un canal de messages directs entre vous et <strong>{users?.[peer]?.full_name ?? peer}</strong>. Consultez leur profil pour en savoir plus.</Text>
                            {/* <Button size='2' variant='ghost' className={'z-1'}>View profile</Button> */}
                        </Flex>
                    }
                </Flex>
            }
        </Box>
    )
}

export const EmptyStateForSavedMessages = () => {
    return (
        <Flex direction='column' className={'pt-24 h-screen px-4'} gap='6'>
            <Heading as='h2' size='7' className="cal-sans">Vos messages sauvegardés apparaîtront ici</Heading>
            <Flex direction='column' gap='1'>
                <Text size='3'>Les messages enregistrés sont un moyen pratique de conserver des informations importantes ou des messages auxquels vous souhaitez vous référer ultérieurement.</Text>
                <Flex align='center' gap='1'>
                    <Text size='3'>Vous pouvez sauvegarder des messages en cliquant simplement sur l'icône du signet.</Text>
                    <BiBookmark />
                    <Text size='3'>dans les actions de messages.</Text>
                </Flex>
            </Flex>
        </Flex>
    )
}

interface ChannelHistoryFirstMessageProps {
    channelID: string
}

export const ChannelHistoryFirstMessage = ({ channelID }: ChannelHistoryFirstMessageProps) => {

    const { channel } = useCurrentChannelData(channelID)
    const { channelMembers, mutate: updateMembers } = useContext(ChannelMembersContext) as ChannelMembersContextType

    if (channel) {
        // depending on whether channel is a DM or a channel, render the appropriate component
        if (channel.type === "dm") {
            return <EmptyStateForDM channelData={channel.channelData} />
        }
        if (updateMembers) {
            return <EmptyStateForChannel channelData={channel.channelData} channelMembers={channelMembers} updateMembers={updateMembers} />
        }
    }

    return null
}