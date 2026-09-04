import { Stack } from 'expo-router';
import { View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import AddSite from '@components/features/auth/AddSite';
import SitesList from '@components/features/auth/SitesList';
import { SafeAreaView } from 'react-native-safe-area-context';
import CommonErrorBoundary from '@components/common/CommonErrorBoundary';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export default function LandingScreen() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()

    return (
        <>
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Stack.Screen options={{ title: t('auth.sites'), headerShown: false }} />
            <SafeAreaView className='flex-1 bg-background'>
                <View className='flex-1 justify-center h-screen pt-24 px-6 gap-3 bg-background'>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-5xl font-cal-sans text-foreground'>{t('common.appName').toLowerCase()}</Text>
                    <View className='h-2' />
                    <SitesList />
                    <AddSite />
                </View>
            </SafeAreaView>
        </>
    );
}

export const ErrorBoundary = CommonErrorBoundary