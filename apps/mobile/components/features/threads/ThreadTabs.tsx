import { useState } from 'react'
import { View } from 'react-native'
import AIThreads from './AIThreads'
import OtherThreads from './OtherThreads'
import ParticipatingThreads from './ParticipatingThreads'
import { SegmentedControl } from '@components/nativewindui/SegmentedControl/SegmentedControl'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

export type ThreadMessage = {
    bot: string,
    channel_id: string,
    content: string,
    creation: string,
    file: string,
    hide_link_preview: 0 | 1,
    image_height: string
    image_width: string,
    is_bot_message: 0 | 1,
    last_message_timestamp: string,
    link_doctype: string,
    link_document: string,
    message_type: "Text" | "Image" | "File" | "Poll",
    name: string,
    owner: string,
    poll_id: string,
    text: string,
    thread_message_id: string,
    participants: { user_id: string }[],
    workspace?: string,
    reply_count?: number
}

const ThreadTabs = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const [selectedIndex, setSelectedIndex] = useState(0)
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
    const values = [t('threads.participating'), t('threads.other'), t('threads.aiAgents')]

    const handleIndexChange = (index: number) => {
        setSelectedIndex(index)
    }

    return (
        <View className='flex-1 flex-col gap-3 pt-4'>
            <View className='px-3'>
                <SegmentedControl
                    values={values}
                    selectedIndex={selectedIndex}
                    onIndexChange={handleIndexChange}
                />
            </View>
            <View>
                {selectedIndex === 0 && <ParticipatingThreads />}
                {selectedIndex === 1 && <OtherThreads />}
                {selectedIndex === 2 && <AIThreads />}
            </View>
        </View>
    )
}

export default ThreadTabs