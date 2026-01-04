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

    // Subscribe to channel events to receive realtime updates
    useFrappeDocumentEventListener('Raven Channel', channelID, () => { })

    // Listen for ai_thread_created event
    useFrappeEventListener('ai_thread_created', (data) => {
        if (data.is_ai_thread && data.thread_id && data.channel_id && channelID === data.channel_id) {
            // Navigate to the AI thread
            goToThread(data.thread_id)
        }
    })

    return null
}

export default AIThreadAutoOpen
