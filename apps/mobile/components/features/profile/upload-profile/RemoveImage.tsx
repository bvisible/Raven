import { Alert, Pressable } from 'react-native'
import { useFrappePostCall } from 'frappe-react-sdk'
import { toast } from 'sonner-native'
import { Text } from '@components/nativewindui/Text'
import TrashIcon from '@assets/icons/TrashIcon.svg'
import { useColorScheme } from '@hooks/useColorScheme'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface RemoveImageProps {
    onSheetClose: (isMutate?: boolean) => void
}

const RemoveImage = ({ onSheetClose }: RemoveImageProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call } = useFrappePostCall('raven.api.raven_users.update_raven_user')

    const removeImage = async () => {
        try {
            await call({
                user_image: ''
            })
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('profile.imageRemoved'))
            onSheetClose()
        } catch (error) {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('profile.imageRemoveFailed'))
        }
    }

    const deleteProfilePicAlert = () =>
        Alert.alert(
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            t('profile.removeImage'),
            t('profile.removeImageConfirm'),
            [
                {
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text: t('common.cancel'),
                    style: 'cancel',
                },
                {
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text: t('common.remove'),
                    style: 'destructive',
                    onPress: removeImage
                },
            ]
        )

    const { isDarkColorScheme } = useColorScheme()

    return (
        <Pressable
            onPress={deleteProfilePicAlert}
            className='flex flex-row w-full items-center gap-2 p-2 rounded-lg ios:active:bg-red-50 dark:ios:active:bg-red-900/30'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <TrashIcon height={20} width={20} fill={isDarkColorScheme ? '#f87171' : '#dc2626'} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-base text-red-600 dark:text-red-400'>{t('profile.removeImage')}</Text>
        </Pressable>
    )
}

export default RemoveImage