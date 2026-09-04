import { useColorScheme } from "@hooks/useColorScheme"
import CameraIcon from "@assets/icons/CameraIcon.svg"
import { CustomFile } from "@raven/types/common/File"
import * as ImagePicker from 'expo-image-picker'
import { ActionButtonLarge } from "./ActionButtonLarge"
import { toast } from "sonner-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const CameraButton = ({ onPick }: { onPick: (files: CustomFile[]) => void }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const takePicture = async () => {
        try {
            let result = await ImagePicker.requestCameraPermissionsAsync().then((r) => {
                if (r.granted) {
                    return ImagePicker.launchCameraAsync({
                        mediaTypes: 'images',
                    })
                } else {
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    toast.error(t('media.cameraPermissionDenied'))
                    return null
                }
            })

            if (result && !result.canceled) {
                const parsedFiles = result.assets.map((asset) => {
                    const id = `captured_image_${Date.now()}.jpg`
                    return {
                        uri: asset.uri,
                        name: asset.fileName ?? id,
                        type: asset.mimeType,
                        size: asset.fileSize,
                        fileID: asset.assetId ?? id,
                    } as any as CustomFile
                })

                onPick(parsedFiles)
            }
        } catch (error) {
            console.error('Error taking picture:', error)
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('media.cameraError'), {
                description: error instanceof Error ? error.message : t('errors.unknownError')
            })
        }
    }

    return (
        <ActionButtonLarge
            icon={<CameraIcon height={20} width={20} color={colors.icon} />}
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            text={t('media.camera')}
            onPress={takePicture}
        />
    )
}

export default CameraButton