import { Text } from '@components/nativewindui/Text'
import { Message } from '@raven/types/common/Message'
import { Link } from 'expo-router'
import { useFrappeGetCall } from 'frappe-react-sdk'
import { Pressable } from 'react-native'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

type Props = {
    message: Message
}

const ViewThreadButton = ({ message }: Props) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    return <Link href={`../../thread/${message.name}`} relativeToDirectory asChild>
        <Pressable hitSlop={10} className='flex flex-row items-center gap-3 border border-border bg-background rounded-lg px-3 py-2 active:bg-card-background/40'>
            <ThreadReplyCount message={message} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-sm text-muted-foreground/80'>{t('messages.viewThread')}</Text>
        </Pressable>
    </Link>
}


const ThreadReplyCount = ({ message }: Props) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { data } = useFrappeGetCall<{ message: number }>("raven.api.threads.get_number_of_replies", {
        thread_id: message.name
    }, ["thread_reply_count", message.name], {
        //// Neoffice - AI thread reply count (9c0248069 + c8f70b230 + ee79d624c, 2026-01-04 "fix(mobile): Fix duplicate reply count and add
        //// AI thread auto-open"). Upstream never revalidates this count, so when Nora answers in a thread
        //// the button kept showing the count from the moment the screen mounted.
        revalidateOnFocus: true,
        revalidateOnMount: true,
        refreshInterval: 0,
        shouldRetryOnError: false
    })
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
    return <Text className='text-sm text-primary dark:text-secondary font-semibold'>{data?.message === 1 ? t('messages.replyCount') : t('messages.repliesCount', { count: data?.message ?? 0 })}</Text>
}

export default ViewThreadButton