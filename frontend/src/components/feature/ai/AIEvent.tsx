import { Loader } from '@/components/common/Loader'
import { Text } from '@radix-ui/themes'
import clsx from 'clsx'
import { useFrappeEventListener } from 'frappe-react-sdk'
import { useEffect, useState } from 'react'

type Props = {
    channelID: string
    //// Neoffice - Nora thinking indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
    onMessageSent?: () => void
}

const AIEvent = ({ channelID }: Props) => {
    //// Neoffice - Nora "is thinking..." indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
    //// Upstream starts with an empty banner and only shows one when a raven_ai_event arrives. Nora
    //// answers in a thread that the client opens itself (AIThreadAutoOpen), and the first event lands
    //// AFTER the navigation - so the user saw an empty thread and thought nothing had happened. The
    //// thread id is handed over through sessionStorage ('ai_thread_thinking', 5 s window) so the new
    //// screen can show the indicator from its first render.
    // Initialize state by checking if this is a new AI thread
    const initializeState = () => {
        const aiThreadInfo = sessionStorage.getItem('ai_thread_thinking');
        if (aiThreadInfo) {
            const info = JSON.parse(aiThreadInfo);
            if (info.threadID === channelID && (Date.now() - info.timestamp) < 5000) {
                sessionStorage.removeItem('ai_thread_thinking');
                return {
                    aiEvent: "Nora is thinking...",
                    showAIEvent: true,
                    isNewThread: true,
                    thinkingStartTime: Date.now()
                };
            }
        }
        return {
            aiEvent: "",
            showAIEvent: false,
            isNewThread: false,
            thinkingStartTime: 0
        };
    };

    const initialState = initializeState();
    const [aiEvent, setAIEvent] = useState(initialState.aiEvent)
    const [showAIEvent, setShowAIEvent] = useState(initialState.showAIEvent)
    const [isNewThread, setIsNewThread] = useState(initialState.isNewThread)
    const [thinkingStartTime, setThinkingStartTime] = useState(initialState.thinkingStartTime)


    useFrappeEventListener("ai_event", (data) => {
        if (data.channel_id === channelID) {
            setAIEvent(data.text)
            setShowAIEvent(true)
            //// Neoffice - Nora thinking indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"): a real event supersedes the
            //// optimistic one and restarts the minimum-display timer.
            setIsNewThread(false) // Reset flag when we get a real event
            setThinkingStartTime(Date.now()) // Reset timer for new thinking messages
        }
    })

    useFrappeEventListener("ai_event_clear", (data) => {
        if (data.channel_id === channelID) {
            //// Neoffice - Nora thinking indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"): a 2 s floor before the banner
            //// can be cleared. Without it a fast local model made the indicator flash for a few frames,
            //// which reads as a glitch rather than as progress.
            const timeSinceThinking = thinkingStartTime ? Date.now() - thinkingStartTime : 0;
            const MIN_DISPLAY_TIME = 2000; // Minimum 2 seconds display time

            // For all messages (including new threads), ensure minimum display time of 2 seconds
            if (thinkingStartTime && timeSinceThinking < MIN_DISPLAY_TIME) {
                // Schedule the clear for later to meet minimum display time
                const remainingTime = MIN_DISPLAY_TIME - timeSinceThinking;
                setTimeout(() => {
                    setAIEvent("")
                    setIsNewThread(false)
                }, remainingTime);
                return;
            }

            // If enough time has passed, clear immediately
            setAIEvent("")
            //// Neoffice - Nora thinking indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
            setIsNewThread(false)
        }
    })


    useEffect(() => {
        //// Neoffice - Nora thinking indicator (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"): upstream hides the banner as
        //// soon as the text is empty, which also killed the optimistic one before its first event.
        if (!aiEvent && showAIEvent) {
            setTimeout(() => {
                setShowAIEvent(false)
            }, 300)
        }
    }, [aiEvent])

    return (
        <div className={clsx(
            'w-full transition-all duration-300 ease-ease-out-quart',
            showAIEvent ? 'translate-y-0 opacity-100 z-50 sm:pb-0 pb-16' : 'translate-y-full opacity-0 h-0'
        )}>
            <div className="flex items-center gap-2 py-2 px-2 bg-white dark:bg-gray-2">
                <Loader />
                <Text size='2'>{aiEvent}</Text>
            </div>
        </div>
    )
}

//// Neoffice - newline at end of file. No code change.
export default AIEvent
