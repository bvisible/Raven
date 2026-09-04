import { ChannelListItem, DMChannelListItem } from "@/utils/channel/ChannelListProvider";
import { useCurrentChannelData } from "@/hooks/useCurrentChannelData";
import { useContext, useMemo } from "react";
import { EditDescriptionButton } from "@/components/feature/channel-details/edit-channel-description/EditDescriptionButton";
import { AddMembersButton } from "@/components/feature/channel-member-details/add-members/AddMembersButton";
import { UserContext } from "@/utils/auth/UserProvider";
import { useGetUserRecords } from "@/hooks/useGetUserRecords";
import { Badge, Box, Flex, Heading, Link, Text } from "@radix-ui/themes";
import { UserAvatar } from "@/components/common/UserAvatar";
import { ChannelIcon } from "@/utils/layout/channelIcon";
import { BiBookmark } from "react-icons/bi";
import { DateMonthYear } from "@/utils/dateConversions";
import { useGetUser } from "@/hooks/useGetUser";
import useFetchChannelMembers from "@/hooks/fetchers/useFetchChannelMembers";
import { useIsUserActive } from "@/hooks/useIsUserActive";
import { replaceCurrentUserFromDMChannelName } from "@/utils/operations";
import { __ } from "@/utils/translations";
//// Add translations for the following strings:

export const EmptyStateForSearch = () => {
    return (
        <Flex justify="center" align="center" className={'w-full h-64'}>
            <Flex direction='column' gap='1' className="text-center">
                {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                    //// French catalogue can carry it. Upstream hardcodes it. */}
                <Text weight="bold" size='5'>{__('Nothing turned up')}</Text>
                <Text as='span' size='2'>{__('You may want to try using different keywords, checking for typos or adjusting your filters.')}</Text>
                <Text as='span' size='2'>
                    {__('Not the results that you expected? File an issue on')}{' '}
                    <Link href="https://github.com/The-Commit-Company/Raven" target="_blank" rel="noreferrer">
                        <Text color='blue' size='2'>GitHub</Text>
                    </Link>.
                </Text>
            </Flex>
        </Flex>
    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    );
};

interface EmptyStateForChannelProps {
    channelData: ChannelListItem,
}

const EmptyStateForChannel = ({ channelData }: EmptyStateForChannelProps) => {

    //// Neoffice - the two hooks below move above the JSX (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad") so the date element
    //// can be built once and interpolated into the translated sentence. Same values, same order.
    const { channelMembers } = useFetchChannelMembers(channelData.name);

    const { currentUser } = useContext(UserContext);
    const users = useGetUserRecords();

    //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): the channel-creation sentence is split around its
    //// date, so the French wording can put the date where French puts it. formattedDate holds the
    //// <DateMonthYear> element the removed inline JSX used to build.
    const formattedDate = <DateMonthYear date={channelData?.creation} />;

    const { isAdmin } = useMemo(() => {
        const channelMember = channelMembers[currentUser]
        return {
            isAdmin: channelMember?.is_admin == 1
        }
    }, [channelMembers, currentUser])

    return (
        <Flex direction='column' className={'p-2'} gap='2'>
            <Flex direction='column' gap='2'>
                <Flex align={'center'} gap='1'>
                    <ChannelIcon type={channelData?.type} />
                    <Heading size='4'>{channelData?.channel_name}</Heading>
                </Flex>
                {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                    //// French catalogue can carry it. Upstream hardcodes it. */}
                <Text size='2'>
                    {users[channelData.owner]?.full_name}{' '}
                    {__('created this channel on')}{' '}
                    {formattedDate}. {__('This is the very beginning of the')}{' '}
                    <strong>{channelData?.channel_name}</strong>{' '}
                    {__('channel.')}</Text>
                {channelData?.channel_description && <Text size={'1'} color='gray'>{channelData?.channel_description}</Text>}
            </Flex>
            {channelData?.is_archived == 0 && isAdmin && <Flex gap='4' className={'z-1'}>
                <EditDescriptionButton channelData={channelData} />
                {channelData?.type !== 'Open' && <AddMembersButton channelData={channelData} />}
            </Flex>}
        </Flex>
    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    );
};

interface EmptyStateForDMProps {
    channelData: DMChannelListItem
}

const EmptyStateForDM = ({ channelData }: EmptyStateForDMProps) => {

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const { currentUser } = useContext(UserContext);

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const peer = channelData.peer_user_id;

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const peerData = useGetUser(peer);

    const { fullName, userImage, isBot } = useMemo(() => {
        //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
        //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
        const isBot = peerData?.type === 'Bot';
        return {
            fullName: peerData?.full_name ?? peer,
            userImage: peerData?.user_image ?? '',
            isBot
        //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
        //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
        };
    }, [peerData, peer]);

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const isActive = useIsUserActive(peer);

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const userName = fullName ?? peer ?? replaceCurrentUserFromDMChannelName(channelData.channel_name, currentUser);

    return (
        <Box className={'p-2'}>
            {channelData?.is_direct_message == 1 &&
                <Flex direction='column' gap='3'>
                    <Flex gap='3' align='center'>
                        <UserAvatar alt={userName} src={userImage} size='3' skeletonSize='7' isBot={isBot} availabilityStatus={peerData?.availability_status} isActive={isActive} />
                        <Flex direction='column' gap='0'>
                            <Heading size='4'>{userName}</Heading>
                            <div>
                                {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                                    //// French catalogue can carry it. Upstream hardcodes it. */}
                                {isBot ? <Badge color='gray' className="py-0 px-1">{__('Bot')}</Badge> : <Text size='1' color='gray'>{peer}</Text>}
                            </div>
                        </Flex>
                    </Flex>
                    {channelData?.is_self_message == 1 ?
                        <Flex direction='column' gap='0'>
                            {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                                //// French catalogue can carry it. Upstream hardcodes it. */}
                            <Text size='2'><strong>{__('This space is all yours.')}</strong> {__('Draft messages, list your to-dos, or keep links and files handy.')} </Text>
                            <Text size='2'>{__('And if you ever feel like talking to yourself, don\'t worry, we won\'t judge - just remember to bring your own banter to the table.')}</Text>
                        </Flex>
                        :
                        <Flex gap='2' align='center'>
                            {peer || fullName ?
                                //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                                //// French catalogue can carry it. Upstream hardcodes it.
                                <Text size='2'>{__('This is a Direct Message channel between you and')} <strong>{fullName ?? peer}</strong>.</Text>
                                :
                                //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                                //// French catalogue can carry it. Upstream hardcodes it.
                                <Text size='2'>{__('We could not find the user for this DM channel')} ({replaceCurrentUserFromDMChannelName(channelData.channel_name, currentUser)}).</Text>
                            }
                        </Flex>
                    }
                </Flex>
            }
        </Box>
    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    );
};

export const EmptyStateForSavedMessages = () => {
    return (
        <Box className={'py-2 px-6'}>
            <Flex direction='column' gap='2'>
                {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                    //// French catalogue can carry it. Upstream hardcodes it. */}
                <Text size='3'><strong>{__('Your saved messages will appear here')}</strong></Text>
                <Flex direction='column' gap='1'>
                    {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                        //// French catalogue can carry it. Upstream hardcodes it. */}
                    <Text size='2' as='span'>{__('Saved messages are a convenient way to keep track of important information or messages you want to refer back to later.')}</Text>
                    <Text size='2' as='span'>
                        {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                            //// French catalogue can carry it. Upstream hardcodes it. */}
                        {__('You can save messages by simply clicking on the bookmark icon')} <BiBookmark className={'-mb-0.5'} /> {__('in message actions.')}
                    </Text>
                </Flex>
            </Flex>
        </Box>
    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    );
};

export const EmptyStateForThreads = () => {
    return (
        <Box className={'py-2 px-6'}>
            <Flex direction='column' gap='2'>
                {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                    //// French catalogue can carry it. Upstream hardcodes it. */}
                <Text size='3'><strong>{__('No threads to show')}</strong></Text>
                <Flex direction='column' gap='1'>
                    {/* //// Neoffice - i18n (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"): English literal wrapped in __() so the
                        //// French catalogue can carry it. Upstream hardcodes it. */}
                    <Text as='span' size='2'>{__('Threads are a way to keep conversations organized and focused. You can create a thread by replying to a message.')}</Text>
                    <Text as='span' size='2'>
                        {__('You can also start a thread by clicking on the')} <strong>{__('Create Thread')}</strong> {__('button on any message.')}
                    </Text>
                </Flex>
            </Flex>
        </Box>
    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    );
};

interface ChannelHistoryFirstMessageProps {
    channelID: string
}

export const ChannelHistoryFirstMessage = ({ channelID }: ChannelHistoryFirstMessageProps) => {

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    const { channel } = useCurrentChannelData(channelID);

    if (channel) {
        // Selon que le canal est un DM ou un canal, rendre le composant approprié
        if (channel.type === "dm") {
            //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
            //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
            return <EmptyStateForDM channelData={channel.channelData} />;
        }
        else {
            //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
            //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
            return <EmptyStateForChannel channelData={channel.channelData} />;
        }
    }

    //// Neoffice - semicolons only, from the formatter that ran with the i18n pass
    //// (a84e3ea68 + 9e0fda334, 2024-10-08 "add trad" / "update trad"). No behaviour change.
    return null;
};
