import AddFileIcon from "@assets/icons/AddFileIcon.svg"
import { useColorScheme } from "@hooks/useColorScheme"
import * as DocumentPicker from 'expo-document-picker'
import { CustomFile } from "@raven/types/common/File"
import { Text } from '@components/nativewindui/Text'
import { Pressable } from "react-native"
import { toast } from "sonner-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface FilePickerButtonProps {
    onPick: (files: CustomFile[]) => void
}

const FilePickerButton = ({ onPick }: FilePickerButtonProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const pickDocument = async () => {
        try {
            let result = await DocumentPicker.getDocumentAsync({
                multiple: true
            })

            if (!result.canceled) {
                const parsedFiles = result.assets.map((asset) => {
                    return {
                        uri: asset.uri,
                        name: asset.name,
                        type: asset.mimeType,
                        size: asset.size,
                        fileID: asset.name + Date.now(),
                    } as any as CustomFile
                })

                onPick(parsedFiles)
            }
        } catch (error) {
            console.error('Error picking documents:', error)
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('media.documentSelectionError'), {
                description: error instanceof Error ? error.message : t('errors.unknownError')
            })
        }
    }

    return (
        <Pressable
            onPress={pickDocument}
            hitSlop={10}
            className='flex flex-row w-full items-center gap-2 p-2 rounded-lg ios:active:bg-linkColor'
            android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
            <AddFileIcon height={20} width={20} color={colors.icon} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-base text-foreground'>{t('media.uploadDocument')}</Text>
        </Pressable>
    )
}

export default FilePickerButton