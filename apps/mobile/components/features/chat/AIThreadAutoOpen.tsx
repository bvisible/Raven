import { useFrappeDocumentEventListener, useFrappeEventListener } from 'frappe-react-sdk'
import { useRouteToThread } from '@hooks/useRouting'

type Props = {
    channelID: string
}

/**
 * Component that listens for AI thread creation events and automatically
 * navigates to the thread when a bot creates one.
 */
const AIThreadAutoOpen = ({ channelID }: Props) => {
    const goToThread = useRouteToThread()

    console.log('[AIThreadAutoOpen] Mounted with channelID:', channelID)

    // Subscribe to channel events to receive realtime updates
    useFrappeDocumentEventListener('Raven Channel', channelID, () => { })

    // Listen for ai_thread_created event
    useFrappeEventListener('ai_thread_created', (data) => {
        console.log('[AIThreadAutoOpen] Event received:', JSON.stringify(data), 'channelID:', channelID)
        if (data.is_ai_thread && data.thread_id && data.channel_id && channelID === data.channel_id) {
            console.log('[AIThreadAutoOpen] Navigating to thread:', data.thread_id)
            goToThread(data.thread_id)
        }
    })

    return null
}

export default AIThreadAutoOpen
