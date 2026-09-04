import { useFrappeFileUpload, useFrappePostCall } from 'frappe-react-sdk'
import { toast } from 'sonner-native'
import ImagePickerButton from '@components/common/Buttons/ImagePickerButton'
import { CustomFile } from '@raven/types/common/File'
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface UploadImageProps {
    onSheetClose: () => void
}

const UploadImage = ({ onSheetClose }: UploadImageProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { myProfile } = useCurrentRavenUser()

    const { call } = useFrappePostCall('raven.api.raven_users.update_raven_user')

    const { upload } = useFrappeFileUpload()

    const uploadImage = async (file: string) => {
        if (file) {
            try {
                await call({
                    user_image: file
                })
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('profile.imageUploaded'))
                onSheetClose()
            } catch (error) {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('profile.imageUploadFailed'))
            }
        }
    }

    const onPick = async (files: CustomFile[]) => {
        const file = files[0]

        if (file) {

            try {
                const res = await upload(file, {
                    doctype: "Raven User",
                    docname: myProfile?.name,
                    fieldname: "user_image",
                    otherData: {
                        optimize: '1',
                    },
                    isPrivate: false,
                })
                await uploadImage(res.file_url)
            } catch (error) {
                console.error(error)
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('profile.imageUploadFailed'))
            }

        }
    }

    return (
        <ImagePickerButton onPick={onPick} allowsMultipleSelection={false} />
    )
}

export default UploadImage