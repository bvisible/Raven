import { Message } from '@raven/types/common/Message'
import { useFrappeDeleteDoc, useSWRConfig } from 'frappe-react-sdk'
import { useCallback } from 'react'
import { Alert } from 'react-native'
import { toast } from 'sonner-native'
import TrashIcon from "@assets/icons/TrashIcon.svg"
import { useColorScheme } from '@hooks/useColorScheme'
import { GetMessagesResponse } from '@raven/types/common/ChatStream'
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface DeleteMessageProps {
    message: Message
    onClose: () => void
}

const DeleteMessage = ({ message, onClose }: DeleteMessageProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { deleteMessage, loading } = useMessageDelete(message, onClose)

    const onDelete = () => {
        deleteMessage()
    }

    const onMessageDelete = useCallback(() => {
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        Alert.alert(t('messages.deleteMessageConfirm'), t('messages.deleteMessageWarning'), [
            { text: t('common.cancel'), style: 'cancel' },
            { text: t('common.delete'), style: 'destructive', onPress: onDelete },
        ])
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t added to the deps so it recomputes on a language switch.
    }, [t])

    const { isDarkColorScheme } = useColorScheme()

    return (
        <ActionButton
            onPress={onMessageDelete}
            icon={<TrashIcon width={18} height={18} fill={isDarkColorScheme ? '#f87171' : '#dc2626'} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('messages.deleteMessage')}
            isDestructive={true}
            disabled={loading}
        />
    )
}

export default DeleteMessage

const useMessageDelete = (message: Message, onDelete: () => void) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { mutate } = useSWRConfig()

    const { deleteDoc, loading } = useFrappeDeleteDoc()

    const deleteMessage = async () => {

        const messageID = message.name
        const channelID = message.channel_id

        const removeMessageFromCache = (data?: GetMessagesResponse): GetMessagesResponse => {

            const existingMessages = data?.message.messages ?? []

            const newMessages = existingMessages.filter((m) => m.name !== messageID)

            return {
                message: {
                    has_old_messages: data?.message.has_old_messages ?? true,
                    has_new_messages: data?.message.has_new_messages ?? false,
                    messages: newMessages
                }
            }
        }



        // Delete the message optimistically
        return mutate({ path: `get_messages_for_channel_${channelID}` }, async (data?: GetMessagesResponse) => {
            // Make the request
            // Call the onDelete callback after the request is made
            // This is because we can close the bottom sheet since we have optimistic updates anyway
            onDelete()
            return deleteDoc('Raven Message', messageID).then(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('messages.messageDeleted'), {
                    duration: 500,
                })
            }).then(() => {
                return removeMessageFromCache(data)
            })
        }, {
            optimisticData: removeMessageFromCache,
            rollbackOnError: true,
            revalidate: false
        }).catch(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('messages.deleteMessageFailed'))
        })
    }
    return { deleteMessage, loading }
}