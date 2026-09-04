import { Pressable } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { useColorScheme } from '@hooks/useColorScheme';
import LogOutIcon from '@assets/icons/LogOutIcon.svg';
import { useLogout } from '@hooks/useLogout';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const LogOutButton = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const { colors } = useColorScheme()

    const onLogout = useLogout()

    return (
        <Pressable onPress={onLogout}
            className="flex flex-row items-center py-3 px-4 rounded-xl justify-between bg-background dark:bg-card ios:active:bg-red-50 dark:ios:active:bg-red-100/10">
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="font-medium text-destructive">{t('auth.logout')}</Text>
            <LogOutIcon height={16} width={16} color={colors.grey} />
        </Pressable>
    )

}

export default LogOutButton