import { TouchableOpacity, View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser';
import useFileURL from '@hooks/useFileURL';
import { Sheet, useSheetRef } from '@components/nativewindui/Sheet';
import { BottomSheetView } from '@gorhom/bottom-sheet';
import RemoveImage from '@components/features/profile/upload-profile/RemoveImage';
import ViewImage from '@components/features/profile/upload-profile/ViewImage';
import UploadImage from '@components/features/profile/upload-profile/UploadImage';
import UserAvatar from '@components/layout/UserAvatar';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const ProfilePicture = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { myProfile, mutate } = useCurrentRavenUser()
    const source = useFileURL(myProfile?.user_image ?? "")
    const bottomSheetRef = useSheetRef()

    const onSheetClose = (isMutate: boolean = true) => {
        bottomSheetRef.current?.close()
        if (isMutate) {
            mutate()
        }
    }

    return (
        <View className="items-center py-3">
            <TouchableOpacity activeOpacity={0.8} onPress={() => bottomSheetRef.current?.present()} className='relative'>
                <UserAvatar
                    src={myProfile?.user_image}
                    alt={`${myProfile?.full_name}`}
                    availabilityStatus={myProfile?.availability_status ? myProfile?.availability_status : 'Available'}
                    imageProps={{ className: 'w-40 h-40' }}
                    fallbackProps={{ className: 'w-40 h-40 border border-border rounded-2xl' }}
                    textProps={{ className: 'text-5xl' }}
                    indicatorProps={{ className: 'w-3 h-3 border-2 border-background' }}
                    avatarProps={{ className: "w-40 h-40" }}
                    borderRadius={16}
                />
            </TouchableOpacity>

            <Sheet ref={bottomSheetRef}>
                <BottomSheetView className='pb-16'>
                    <View className="flex-col gap-3">
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className="text-xl font-cal-sans px-5">{t('profile.updateProfilePicture')}</Text>
                        <View className="flex-col justify-start items-start px-3 w-full">
                            <UploadImage onSheetClose={onSheetClose} />
                            {source ? <ViewImage uri={source?.uri ?? ""} onSheetClose={onSheetClose} /> : null}
                            {source ? <RemoveImage onSheetClose={onSheetClose} /> : null}
                        </View>
                    </View>
                </BottomSheetView>
            </Sheet>
        </View>
    )
}

export default ProfilePicture