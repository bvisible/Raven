import { router } from 'expo-router'
import { Text } from '@components/nativewindui/Text'
import { useColorScheme } from '@hooks/useColorScheme'
import EyeIcon from '@assets/icons/EyeIcon.svg'
import { Pressable } from 'react-native'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface ViewImageProps {
    uri: string
    onSheetClose: (isMutate?: boolean) => void
}

const ViewImage = ({ uri, onSheetClose }: ViewImageProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const openViewer = () => {
        router.push({
            pathname: `./../../chat/[id]/file-viewer`,
            params: { uri }
        }, { relativeToDirectory: true })
        onSheetClose(false)
    }

    return (
        <Pressable
            onPress={openViewer}
            className='flex flex-row w-full items-center gap-2 p-2 rounded-lg ios:active:bg-linkColor'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <EyeIcon height={20} width={20} color={colors.icon} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-base text-foreground'>{t('media.viewImage')}</Text>
        </Pressable>
    )
}

export default ViewImage