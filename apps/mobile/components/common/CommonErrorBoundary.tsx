import { Link, type ErrorBoundaryProps } from 'expo-router';
import { Text } from '@components/nativewindui/Text';
import { ScrollView, TouchableOpacity, View } from 'react-native';
import ErrorIcon from '@assets/icons/ErrorIcon.svg'
import { useColorScheme } from '@hooks/useColorScheme';
import { Divider } from '@components/layout/Divider';
import { toast } from 'sonner-native';
import * as Clipboard from 'expo-clipboard'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export function CommonErrorBoundary({ error, retry }: ErrorBoundaryProps) {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const onCopy = async () => {
        await Clipboard.setStringAsync(error.message + '\n' + error.stack)
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        toast.success(t('errors.errorCopied'))
    }

    return (
        <View className='flex-1 gap-2 py-8 px-4 justify-center items-center bg-background'>
            <ErrorIcon width={100} height={100} fill={colors.icon} />
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className='text-foreground text-xl font-semibold'>{t('errors.unexpectedError')}</Text>
            <Text className='text-foreground'>{error.message}</Text>
            <View className='flex items-center gap-2 pt-4'>
                <TouchableOpacity onPress={retry} className='bg-foreground rounded-lg px-4 py-2'>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-background text-sm font-medium'>{t('errors.reloadPage')}</Text>
                </TouchableOpacity>

                <View className='flex gap-2 items-center'>
                    <Link href="https://github.com/The-Commit-Company/raven/issues" target='_blank' className='bg-card-background rounded-lg px-4 py-2'>
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className='text-foreground text-sm font-medium'>{t('errors.reportIssue')}</Text>
                    </Link>
                    <TouchableOpacity onPress={onCopy} className='bg-card-background rounded-lg px-4 py-2'>
                        <Text className='text-foreground text-center w-full text-sm font-medium'>
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            {t('errors.copyError')}
                        </Text>
                    </TouchableOpacity>
                </View>
            </View>
            <Divider />
            <ScrollView>
                <Text className='text-muted-foreground text-xs'>
                    {error.stack}
                </Text>
            </ScrollView>
        </View>
    );
}
export default CommonErrorBoundary