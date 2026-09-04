import { Keyboard, View } from 'react-native'
import { Message } from '@raven/types/common/Message'
import TiptapEditor from '@components/features/chat/ChatInput/TiptapEditor/TiptapEditor'
import { Button } from '@components/nativewindui/Button'
import { Text } from '@components/nativewindui/Text'
import { useColorScheme } from '@hooks/useColorScheme'
import { useRef } from 'react'
import { useFrappeUpdateDoc } from 'frappe-react-sdk'
import { toast } from 'sonner-native'
import ErrorBanner from '@components/common/ErrorBanner'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface EditMessageSheetProps {
    message: Message;
    onClose: () => void
    onUpdate?: (content: string, json: any) => Promise<void>
}


const EditMessageSheet = ({ message, onClose }: EditMessageSheetProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors, isDarkColorScheme } = useColorScheme()

    const { updateDoc, error, loading: updatingDoc } = useFrappeUpdateDoc()

    // store message text in a ref
    const messageTextRef = useRef(message.text || '')

    const handleUpdate = (html: string) => {
        messageTextRef.current = html
    }

    const handleSave = async () => {
        updateDoc('Raven Message', message.name,
            { text: messageTextRef.current }).then((d) => {
                Keyboard.dismiss()
                onClose()
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('messages.messageUpdated'))
            })
    };
    return (
        <View className="flex flex-col gap-3 px-4 pt-2">

            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-lg font-cal-sans ml-0.5'>{t('messages.editMessage')}</Text>

            {error ? <ErrorBanner error={error} /> : null}

            <TiptapEditor
                content={message.text || ''}
                dom={{
                    scrollEnabled: true,
                    focusable: true,
                    containerStyle: {
                        padding: 8,
                        height: 'auto',
                        minHeight: 200,
                        borderWidth: 1,
                        borderRadius: 10,
                        borderColor: colors.grey4,
                        overflowX: 'hidden',
                    },
                }}
                isDarkMode={isDarkColorScheme}
                onUpdate={handleUpdate}
            />
            <Button
                variant='primary'
                size='lg'
                onPress={handleSave}
                disabled={updatingDoc}>
                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                <Text>{updatingDoc ? t('common.updating') : t('common.update')}</Text>
            </Button>
        </View>
    )
}

export default EditMessageSheet