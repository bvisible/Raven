import { useColorScheme } from '@hooks/useColorScheme'
import { Message } from '@raven/types/common/Message'
import EditIcon from "@assets/icons/EditIcon.svg"
import EditMessageSheet from './EditMessageSheet'
import { Sheet, useSheetRef } from '@components/nativewindui/Sheet'
import { BottomSheetView } from '@gorhom/bottom-sheet'
import ActionButton from '@components/common/Buttons/ActionButton'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface EditMessageActionProps {
    message: Message
    onClose: () => void
}

const EditMessageAction = ({ message, onClose }: EditMessageActionProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const editSheetRef = useSheetRef()

    const handlePress = () => {
        editSheetRef.current?.present()
    }

    const handleClose = () => {
        // close both the edit sheet and the message actions sheet
        editSheetRef.current?.dismiss()

        setTimeout(() => {
            onClose()
        }, 100)
    }

    const handleDismiss = () => {
        onClose()
    }

    return (
        <>
            {/* <Pressable
                onPress={handlePress}
                className='flex flex-row items-center gap-3 p-2 rounded-lg ios:active:bg-linkColor'
                android_ripple={{ color: 'rgba(0,0,0,0.1)', borderless: false }}>
                <EditIcon width={18} height={18} stroke={colors.icon} fillOpacity={0} />
                <Text className='text-base text-foreground'>Edit</Text>
            </Pressable> */}
            <ActionButton
                onPress={handlePress}
                icon={<EditIcon width={18} height={18} stroke={colors.icon} fillOpacity={0} />}
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                text={t('common.edit')}
            />

            <Sheet enableDynamicSizing={false} ref={editSheetRef} snapPoints={['90']} enableDismissOnClose onDismiss={handleDismiss}>
                <BottomSheetView className='pb-8'>
                    <EditMessageSheet
                        message={message}
                        onClose={handleClose}
                    />
                </BottomSheetView>
            </Sheet>
        </>
    )
}

export default EditMessageAction