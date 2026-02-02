import { Loader } from '@/components/common/Loader'
import { Text, Box } from '@radix-ui/themes'
import clsx from 'clsx'
import { useFrappeEventListener } from 'frappe-react-sdk'
import { useEffect, useState, useRef } from 'react'
import { BiChevronDown, BiChevronRight, BiBrain } from 'react-icons/bi'

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

    // Thinking/reasoning state
    const [isThinking, setIsThinking] = useState(false)
    const [thinkingContent, setThinkingContent] = useState("")
    const [showThinkingContent, setShowThinkingContent] = useState(false)

    useFrappeEventListener("ai_event", (data) => {
        if (data.channel_id === channelID) {
            setAIEvent(data.text)
            setShowAIEvent(true)
            setIsNewThread(false)
            setThinkingStartTime(Date.now())
            // Reset streaming when a new thinking event comes in
            setStreamedText("")
            setIsStreaming(false)
            setIsThinking(false)
            setThinkingContent("")
        }
    })

    useFrappeEventListener("ai_event_clear", (data) => {
        if (data.channel_id === channelID) {
            const timeSinceThinking = thinkingStartTime ? Date.now() - thinkingStartTime : 0;
            const MIN_DISPLAY_TIME = 500;

            if (thinkingStartTime && timeSinceThinking < MIN_DISPLAY_TIME && !isStreaming) {
                const remainingTime = MIN_DISPLAY_TIME - timeSinceThinking;
                setTimeout(() => {
                    setAIEvent("")
                    setIsNewThread(false)
                }, remainingTime);
                return;
            }

            setAIEvent("")
            setIsNewThread(false)
        }
    })

    // Listen for thinking start
    useFrappeEventListener("ai_thinking_start", (data) => {
        if (data.channel_id === channelID) {
            setIsThinking(true)
            setThinkingContent("")
            setShowAIEvent(true)
            setAIEvent("") // Clear "thinking" text, we'll show reasoning indicator
        }
    })

    // Listen for thinking end (includes captured thinking content)
    useFrappeEventListener("ai_thinking_end", (data) => {
        if (data.channel_id === channelID) {
            setIsThinking(false)
            if (data.thinking_content) {
                setThinkingContent(data.thinking_content)
            }
        }
    })

    // Listen for streaming tokens
    useFrappeEventListener("ai_token", (data) => {
        if (data.channel_id === channelID) {
            setIsStreaming(true)
            setShowAIEvent(true)
            setAIEvent("")
            setStreamedText(prev => prev + data.token)
        }
    })

    // Listen for stream end
    useFrappeEventListener("ai_stream_done", (data) => {
        if (data.channel_id === channelID) {
            setTimeout(() => {
                setIsStreaming(false)
                setStreamedText("")
                setShowAIEvent(false)
                setIsThinking(false)
                setThinkingContent("")
                setShowThinkingContent(false)
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
        if (!aiEvent && !isStreaming && !isThinking && showAIEvent) {
            setTimeout(() => {
                setShowAIEvent(false)
            }, 300)
        }
    }, [aiEvent, isStreaming, isThinking])

    // Show either thinking indicator, reasoning indicator, or streaming text
    const hasContent = aiEvent || isThinking || (isStreaming && streamedText)

    return (
        <div className={clsx(
            'w-full transition-all duration-300 ease-ease-out-quart',
            showAIEvent && hasContent ? 'translate-y-0 opacity-100 z-50 sm:pb-0 pb-16' : 'translate-y-full opacity-0 h-0'
        )}>
            <div className="py-2 px-2 bg-white dark:bg-gray-2">
                {/* Initial thinking indicator (before streaming starts) */}
                {aiEvent && !isStreaming && !isThinking && (
                    <div className="flex items-center gap-2">
                        <Loader />
                        <Text size='2'>{aiEvent}</Text>
                    </div>
                )}

                {/* Reasoning/thinking indicator */}
                {isThinking && (
                    <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
                        <BiBrain className="w-4 h-4 animate-pulse" />
                        <Text size='2' weight="medium">Reasoning...</Text>
                    </div>
                )}

                {/* Captured thinking content (collapsible) */}
                {!isThinking && thinkingContent && (
                    <div className="mb-2">
                        <button
                            onClick={() => setShowThinkingContent(!showThinkingContent)}
                            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                        >
                            {showThinkingContent ? (
                                <BiChevronDown className="w-4 h-4" />
                            ) : (
                                <BiChevronRight className="w-4 h-4" />
                            )}
                            <BiBrain className="w-3 h-3" />
                            <span>Reasoning</span>
                        </button>
                        {showThinkingContent && (
                            <Box className="mt-1 p-2 bg-purple-50 dark:bg-purple-900/20 rounded text-xs text-gray-600 dark:text-gray-300 max-h-32 overflow-y-auto">
                                <pre className="whitespace-pre-wrap font-mono">{thinkingContent}</pre>
                            </Box>
                        )}
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
