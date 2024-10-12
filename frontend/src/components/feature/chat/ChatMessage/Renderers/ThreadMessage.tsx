import { Link } from "react-router-dom"
import { Message } from "../../../../../../../types/Messaging/Message"
import { Button, Flex, Text } from "@radix-ui/themes"
import { useFrappeGetDocCount } from "frappe-react-sdk"
import { RavenMessage } from "@/types/RavenMessaging/RavenMessage"
import { useFrappeDocumentEventListener } from "frappe-react-sdk"
import { useFrappeEventListener } from "frappe-react-sdk"
import { __ } from '@/utils/translations'
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
//// add trad and auto open thread si bot
////
export const ThreadMessage = ({ thread, isBot }: { thread: Message, isBot: boolean }) => {
    const navigate = useNavigate();

    const { data } = useFrappeGetDocCount<RavenMessage>("Raven Message", [["channel_id", "=", thread.name]], undefined, undefined, undefined, {
        revalidateOnFocus: false,
        shouldRetryOnError: false,
        keepPreviousData: false
    });

    useEffect(() => {
        if (isBot || (data !== undefined && data === 0)) {
            navigate(`/channel/${thread.channel_id}/thread/${thread.name}`);
        }
    }, [isBot, data, navigate, thread.channel_id, thread.name]);
    ////

    return (
        <div className="mt-2">
            <Flex justify={'between'} align={'center'} gap='2' className="w-fit px-3 py-2 border border-gray-4 rounded-md shadow-[0_20px_30px_-10px_rgba(0,0,0,0.1)]">
                <ThreadReplyCount thread={thread} />
                <Button size={'1'}
                    asChild
                    color="gray"
                    variant={'ghost'}
                    className={'not-cal w-fit hover:bg-transparent hover:underline cursor-pointer'}>
                    <Link to={`/channel/${thread.channel_id}/thread/${thread.name}`}>{__('View Thread')}</Link>
                </Button>
            </Flex>
        </div>
    )
}

export const ThreadReplyCount = ({ thread }: { thread: Message }) => {

    const { data, mutate } = useFrappeGetDocCount<RavenMessage>("Raven Message", [["channel_id", "=", thread.name]], undefined, undefined, undefined, {
        revalidateOnFocus: false,
        shouldRetryOnError: false,
        keepPreviousData: false
    })

    // Listen to realtime event for new message count
    useFrappeDocumentEventListener('Raven Message', thread.name, () => { })

    useFrappeEventListener('thread_reply_created', () => {
        mutate()
    })

    return <Flex gap='1' align={'center'}>
        <Text size='1' className={'font-semibold text-accent-a11'}>{data ?? 0}</Text>
        <Text size='1' className={'font-semibold text-accent-a11'}>{data && data === 1 ? __('Reply') : __('Replies')}</Text>
    </Flex>
}