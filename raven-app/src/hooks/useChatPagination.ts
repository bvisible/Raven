import { useFrappeGetCall } from "frappe-react-sdk"
import { useState } from "react"
import { Message } from "../../../types/Messaging/Message"

/**
 * Hook to paginate chat messages
 * 
 * 1. By default, fetch the latest 40 messages from the channel
 * 2. When a message add event is received, fetch the new messages and append (and merge) them to the existing messages
 * 3. When a message delete event is received, remove the message from the list
 * 4. When a message update event is received, update the message in the list
 * 5. Callback function to fetch older messages - deduped and debounced to avoid multiple requests
 * 
 * @param channelId 
 * @param baseMessage
 */
const useChatPagination = (channelId: string, baseMessage?: string) => {

    const [messages, setMessages] = useState<Message[]>([])

    /**
     * Add/update messages in the list
     * @param newMessages 
     */
    const addToMessages = (newMessages: Message[]) => {
        setMessages((prevMessages) => {
            // Merge new messages with existing messages
            const mergedMessages = prevMessages
            newMessages.forEach((newMessage) => {
                const index = mergedMessages.findIndex((message) => message.name === newMessage.name)
                if (index === -1) {
                    mergedMessages.push(newMessage)
                } else {
                    mergedMessages[index] = newMessage
                }
            })

            // Sort the messages by date in ascending order
            mergedMessages.sort((a, b) => {
                return new Date(a.creation).getTime() - new Date(b.creation).getTime()
            })

            return mergedMessages.map((message) => ({ ...message, key: `${message.name}_${message.modified}` }))
        })
    }
    // Latest messages are fetched by default in useFrappeGetCall
    const { data, isLoading } = useFrappeGetCall('raven.api.chat.get_latest_messages', {
        channel_id: channelId
    }, `get_latest_messages_${channelId}`, {
        revalidateOnFocus: false,
        // keepPreviousData: true,
        onSuccess: (data) => {
            //TODO: This does not fire all the time
            // console.log("Fired")
            addToMessages(data.message)
        },

    })

    const [loadingOlderMessages, setLoadingOlderMessages] = useState(false)

    /**
     * Fetch older messages if a request is not already in progress.
     */
    const loadOlderMessages = () => {
        if (loadingOlderMessages) return
        setLoadingOlderMessages(true)
        // TODO: Fetch older messages
        setLoadingOlderMessages(false)
    }

    const loadLatestMessages = () => {
    }

    return {
        messages,
        isLoading
    }
}

export default useChatPagination