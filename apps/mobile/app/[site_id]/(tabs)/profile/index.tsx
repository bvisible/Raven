import { Stack } from 'expo-router';
import { Platform, ScrollView, View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import LogOutButton from '@components/features/profile/profile-settings/LogOutButton';
import NotificationSetting from '@components/features/profile/profile-settings/NotificationSetting';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AppearanceSetting from '@components/features/profile/profile-settings/AppearanceSetting';
import UserAvailability from '@components/features/profile/profile-settings/UserAvailability';
import UserFullName from '@components/features/profile/profile-settings/UserFullName';
import CustomStatus from '@components/features/profile/profile-settings/CustomStatus';
import ProfilePicture from '@components/features/profile/upload-profile/ProfilePicture';
import { nativeApplicationVersion, nativeBuildVersion } from 'expo-application';
import Preferences from '@components/features/profile/profile-settings/Preferences';
import SwitchSitesSetting from '@components/features/profile/profile-settings/SwitchSitesSetting';
//// Neoffice - language picker (13161f9f1, 2026-01-04 "feat(mobile): Add language selection page"):
//// the profile screen gets a Language row; upstream has no language setting at all.
import LanguageSetting from '@components/features/profile/profile-settings/LanguageSetting';
import CommonErrorBoundary from '@components/common/CommonErrorBoundary';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const SCREEN_OPTIONS = {
    title: 'Profile',
    headerTransparent: Platform.OS === 'ios',
    headerBlurEffect: 'systemMaterial',
} as const

export default function Profile() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const insets = useSafeAreaInsets()

    return (
        <>
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): upstream passes the frozen SCREEN_OPTIONS object, whose
                //// title is a hardcoded English literal. Spread it and override title with t() so the header
                //// follows the chosen language. */}
            <Stack.Screen options={{
                ...SCREEN_OPTIONS,
                title: t('profile.profile'),
            }} />
            <View className='flex-1 px-4'>
                <ScrollView
                    contentInsetAdjustmentBehavior="automatic"
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={{ paddingBottom: insets.bottom }}>
                    <View className='flex flex-col gap-4 mt-1.5'>
                        <ProfilePicture />
                        <View className='flex flex-col gap-0.5'>
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <Text className='pl-2 pb-1 text-xs text-muted-foreground/80'>{t('profile.personalInfo')}</Text>
                            <UserFullName />
                            <CustomStatus />
                            <UserAvailability />
                        </View>
                        <View className='flex flex-col gap-0.5'>
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <Text className='pl-2 pb-1 text-xs text-muted-foreground/80'>{t('profile.preferences')}</Text>
                            <NotificationSetting />
                            <AppearanceSetting />
                            {/* //// Neoffice - language picker (13161f9f1, 2026-01-04): the row that opens ./language. */}
                            <LanguageSetting />
                            <Preferences />
                            <SwitchSitesSetting />
                        </View>
                        <LogOutButton />
                        <View className='flex flex-col justify-center items-center pt-2 gap-1'>
                            {/* //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): the app is published as Synk. */}
                            <Text className='text-lg text-muted-foreground/90 font-cal-sans'>synk</Text>
                            <View className='flex flex-col items-center justify-center'>
                                {/* //// Neoffice - rebrand + i18n (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk" / e9ee1845e, 2026-01-04): credit line names both
                                    //// publishers, and "Version" goes through t(). */}
                                <Text className='text-xs text-muted-foreground/80'>by The Commit Company and Neoservice</Text>
                                <Text className='text-xs text-muted-foreground/80'>{t('common.version')} {nativeApplicationVersion} ({nativeBuildVersion})</Text>
                            </View>
                        </View>
                    </View>
                </ScrollView>
            </View>
        </>
    )
}

export const ErrorBoundary = CommonErrorBoundary