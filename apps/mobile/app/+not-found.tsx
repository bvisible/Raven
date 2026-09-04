import { router, Stack } from 'expo-router';
import { View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { useAsyncStorage } from '@react-native-async-storage/async-storage';
import { Button } from '@components/nativewindui/Button';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export default function NotFoundScreen() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { getItem } = useAsyncStorage(`default-site`)

    const handleGoHome = () => {
        getItem().then(site => {
            if (site) {
                router.replace(`/${site}`)
            } else {
                router.replace('/landing')
            }
        })
    }
    return (
        <>
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Stack.Screen options={{ title: t('errors.oops') }} />
            <View className='flex-1 bg-background justify-center gap-3 items-center'>
                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                <Text className='text-3xl text-foreground'>{t('errors.screenNotFound')}</Text>
                <View className='h-2' />
                <Button onPress={handleGoHome}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text>{t('common.goHome')}</Text>
                </Button>
            </View>
        </>
    );
}