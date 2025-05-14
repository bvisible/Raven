import { RavenMessage } from '@/types/RavenMessaging/RavenMessage'
import { useFrappePostCall } from 'frappe-react-sdk'
import { Message } from '../../../../../../types/Messaging/Message'

export const useSendMessage = (channelID: string, uploadFiles: (selectedMessage?: Message | null, threadMessageId?: string | null) => Promise<RavenMessage[]>, onMessageSent: (messages: RavenMessage[]) => void, selectedMessage?: Message | null) => {

    const { call, loading } = useFrappePostCall<{ message: RavenMessage }>('raven.api.raven_message.send_message')

    const sendMessage = async (content: string, json?: any, sendSilently: boolean = false): Promise<void> => {

        if (content) {
            return call({
                channel_id: channelID,
                text: content,
                json_content: json,
                is_reply: selectedMessage ? 1 : 0,
                linked_message: selectedMessage ? selectedMessage.name : null,
                send_silently: sendSilently ? true : false
            })
                .then((res) => onMessageSent([res.message]))
                .then(() => uploadFiles())
                .then((res) => {
                    onMessageSent(res)
                })
        } else {
            return uploadFiles(selectedMessage)
                .then((res) => {
                    onMessageSent(res)
                })
                .catch(error => {
                    console.error("Error uploading files:", error);
                    throw error;
                });
        } 
    }


    return {
        sendMessage,
        loading
    }
}