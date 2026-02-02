import { Loader } from '@/components/common/Loader'
import { Text } from '@radix-ui/themes'
import clsx from 'clsx'
import { useFrappeEventListener } from 'frappe-react-sdk'
import { useEffect, useState, useRef } from 'react'

type Props = {
    channelID: string
    onMessageSent?: () => void
}

const AIEvent = ({ channelID }: Props) => {
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

    // Streaming state
    const [streamedText, setStreamedText] = useState("")
    const [isStreaming, setIsStreaming] = useState(false)
    const streamContainerRef = useRef<HTMLDivElement>(null)

    useFrappeEventListener("ai_event", (data) => {
        if (data.channel_id === channelID) {
            setAIEvent(data.text)
            setShowAIEvent(true)
            setIsNewThread(false)
            setThinkingStartTime(Date.now())
            // Reset streaming when a new thinking event comes in
            setStreamedText("")
            setIsStreaming(false)
        }
    })

    useFrappeEventListener("ai_event_clear", (data) => {
        if (data.channel_id === channelID) {
            const timeSinceThinking = thinkingStartTime ? Date.now() - thinkingStartTime : 0;
            const MIN_DISPLAY_TIME = 500; // Reduced to 500ms since streaming provides visual feedback

            if (thinkingStartTime && timeSinceThinking < MIN_DISPLAY_TIME && !isStreaming) {
                const remainingTime = MIN_DISPLAY_TIME - timeSinceThinking;
                setTimeout(() => {
                    setAIEvent("")
                    setIsNewThread(false)
                }, remainingTime);
                return;
            }

            // Clear thinking text immediately when streaming starts
            setAIEvent("")
            setIsNewThread(false)
        }
    })

    // Listen for streaming tokens
    useFrappeEventListener("ai_token", (data) => {
        if (data.channel_id === channelID) {
            setIsStreaming(true)
            setShowAIEvent(true)
            setAIEvent("") // Clear "thinking" message when tokens arrive
            setStreamedText(prev => prev + data.token)
        }
    })

    // Listen for stream end
    useFrappeEventListener("ai_stream_done", (data) => {
        if (data.channel_id === channelID) {
            // Keep streaming text visible briefly, then clear
            setTimeout(() => {
                setIsStreaming(false)
                setStreamedText("")
                setShowAIEvent(false)
            }, 300)
        }
    })

    // Auto-scroll streaming container
    useEffect(() => {
        if (streamContainerRef.current && isStreaming) {
            streamContainerRef.current.scrollTop = streamContainerRef.current.scrollHeight
        }
    }, [streamedText, isStreaming])

    useEffect(() => {
        if (!aiEvent && !isStreaming && showAIEvent) {
            setTimeout(() => {
                setShowAIEvent(false)
            }, 300)
        }
    }, [aiEvent, isStreaming])

    // Show either thinking indicator or streaming text
    const hasContent = aiEvent || (isStreaming && streamedText)

    return (
        <div className={clsx(
            'w-full transition-all duration-300 ease-ease-out-quart',
            showAIEvent && hasContent ? 'translate-y-0 opacity-100 z-50 sm:pb-0 pb-16' : 'translate-y-full opacity-0 h-0'
        )}>
            <div className="py-2 px-2 bg-white dark:bg-gray-2">
                {/* Thinking indicator */}
                {aiEvent && !isStreaming && (
                    <div className="flex items-center gap-2">
                        <Loader />
                        <Text size='2'>{aiEvent}</Text>
                    </div>
                )}

                {/* Streaming text display */}
                {isStreaming && streamedText && (
                    <div
                        ref={streamContainerRef}
                        className="max-h-48 overflow-y-auto"
                    >
                        <Text size='2' className="whitespace-pre-wrap leading-relaxed">
                            {streamedText}
                            <span className="inline-block w-2 h-4 ml-0.5 bg-gray-800 dark:bg-gray-200 animate-pulse" />
                        </Text>
                    </div>
                )}
            </div>
        </div>
    )
}

export default AIEvent
