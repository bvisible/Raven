import { useCallback, useState } from 'react'
import { useFrappeGetCall, useFrappePostCall } from 'frappe-react-sdk'
import { Message } from '@raven/types/common/Message'
import { Poll } from '../Renderers/PollMessage'
import { toast } from 'sonner-native'
import ArrowBackRetractIcon from "@assets/icons/ArrowBackRetractIcon.svg"
import { useColorScheme } from '@hooks/useColorScheme'
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface RetractVoteProps {
    message: Message
    onClose: () => void
}

const RetractVote = ({ message, onClose }: RetractVoteProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { retractVote, poll_data } = useRetractVote(message)
    const { colors } = useColorScheme()

    if (poll_data && poll_data?.message.current_user_votes.length > 0)
        return (
            <ActionButton
                onPress={() => retractVote(onClose)}
                icon={<ArrowBackRetractIcon width={18} height={18} fill={colors.icon} />}
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                text={t('polls.retractVote')}
            />
        )

    return null
}

export default RetractVote

const useRetractVote = (message: Message) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const [isLoading, setIsLoading] = useState(false)

    const { data: poll_data } = useFrappeGetCall<{ message: Poll }>('raven.api.raven_poll.get_poll', {
        'message_id': message?.name,
    }, `poll_data_${message?.poll_id}`, {
        revalidateOnFocus: false,
        revalidateOnReconnect: false
    })

    const { call } = useFrappePostCall('raven.api.raven_poll.retract_vote')

    const retractVote = useCallback(async (onSuccess: () => void) => {
        setIsLoading(true)
        try {
            await call({
                poll_id: message?.poll_id,
            })
            onSuccess()
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('polls.voteRetracted'))
            setIsLoading(false)
        } catch (e: unknown) {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('polls.voteRetractFailed'))
        }
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t added to the deps so it recomputes on a language switch.
    }, [message, t])

    return { retractVote, poll_data, isLoading }
}