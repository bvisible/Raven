import { View } from 'react-native';
import { Stack } from 'expo-router';
import ThreadTabs from '@components/features/threads/ThreadTabs';
import { useColorScheme } from '@hooks/useColorScheme';
import CommonErrorBoundary from '@components/common/CommonErrorBoundary';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export default function Threads() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const { colors } = useColorScheme()

    return (
        <>
            <Stack.Screen options={{
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                title: t('threads.threads'),
                headerLargeTitle: false,
                headerStyle: { backgroundColor: colors.background },
            }} />
            <View className='flex-1 pb-24'>
                <ThreadTabs />
            </View>
        </>
    )
}

export const ErrorBoundary = CommonErrorBoundary