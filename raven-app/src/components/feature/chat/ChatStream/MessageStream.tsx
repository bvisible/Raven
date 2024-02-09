import useChatPagination from '@/hooks/useChatPagination'
import React, { Profiler, ProfilerOnRenderCallback, Suspense, useRef } from 'react'
import MessageItem from '../ChatMessage/MessageItem'
import { Box } from '@radix-ui/themes'
import { useLocation, useParams } from 'react-router-dom'

type Props = {
    channelID: string
}
const MessageStream = () => {

    const { channelID } = useParams()
    const { messages, isLoading } = useChatPagination(channelID)
    const boxRef = useRef<HTMLDivElement>(null)

    const onRender: ProfilerOnRenderCallback = (id, phase, actualDuration, baseDuration, startTime, commitTime, interactions) => {
        if (id === 'MessageItem_3b5b198af9')
            console.log(id, phase, actualDuration, baseDuration, startTime, commitTime, interactions)
    }

    // console.log('messages', messages)
    return (
        <div ref={boxRef} className='overflow-y-scroll h-full'>
            {messages.map((message) => {
                return <Box className="w-full overflow-x-clip text-ellipsis" key={message.key}>
                    <MessageItem
                        message={message}
                        isScrolling={false}
                        updateMessages={() => { }}
                        onReplyMessageClick={() => { }}
                        setEditMessage={() => { }}
                        replyToMessage={() => { }}
                        setDeleteMessage={() => { }} />
                </Box>
            })}
            {isLoading && <p>Loading...</p>}
            No.of messages: {messages.length}<br />
            MessageStream for {channelID}

        </div>
    )
}

export default MessageStream