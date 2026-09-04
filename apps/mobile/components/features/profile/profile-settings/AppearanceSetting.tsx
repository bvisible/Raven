import { View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import { useColorScheme } from '@hooks/useColorScheme';
import PaletteIcon from '@assets/icons/PaletteIcon.svg'
import * as DropdownMenu from 'zeego/dropdown-menu'
import { useMemo } from 'react';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const AppearanceSetting = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const { colors } = useColorScheme()
    const { themeValue, setColorScheme } = useColorScheme()

    const themeDisplay = useMemo(() => {
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): upstream returns the English theme names directly.
        if (themeValue === 'light') return t('settings.lightTheme')
        if (themeValue === 'dark') return t('settings.darkTheme')
        if (themeValue === 'system') return t('settings.systemTheme')
        return t('settings.lightTheme')
    }, [themeValue, t])

    return (
        <View>
            <View className='flex flex-row py-2.5 px-4 rounded-xl justify-between bg-background dark:bg-card'>
                <View className='flex-row items-center gap-2'>
                    <PaletteIcon height={18} width={18} color={colors.icon} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base'>{t('profile.appearance')}</Text>
                </View>
                <DropdownMenu.Root>
                    <DropdownMenu.Trigger>
                        <Text className='text-base text-muted-foreground/80'>{themeDisplay}</Text>
                    </DropdownMenu.Trigger>
                    <DropdownMenu.Content side='bottom' align='end'>
                        <DropdownMenu.Item key="light" onSelect={() => setColorScheme('light')}>
                            <DropdownMenu.ItemIcon ios={{
                                name: 'sun.max', // Sun icon for light mode
                                pointSize: 16,
                                scale: 'medium',
                                hierarchicalColor: {
                                    dark: 'gray',
                                    light: 'gray',
                                },
                            }} />
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <DropdownMenu.ItemTitle>{t('settings.lightTheme')}</DropdownMenu.ItemTitle>
                        </DropdownMenu.Item>
                        <DropdownMenu.Item key="dark" onSelect={() => setColorScheme('dark')}>
                            <DropdownMenu.ItemIcon ios={{
                                name: 'moon', // Moon icon for dark mode
                                pointSize: 16,
                                scale: 'medium',
                                hierarchicalColor: {
                                    dark: 'gray',
                                    light: 'gray',
                                },
                            }} />
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <DropdownMenu.ItemTitle>{t('settings.darkTheme')}</DropdownMenu.ItemTitle>
                        </DropdownMenu.Item>
                        <DropdownMenu.Item key="system" onSelect={() => setColorScheme('system')}>
                            <DropdownMenu.ItemIcon ios={{
                                name: 'circle.lefthalf.filled',
                                pointSize: 16,
                                scale: 'medium',
                                hierarchicalColor: {
                                    dark: 'gray',
                                    light: 'gray',
                                },
                            }} />
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <DropdownMenu.ItemTitle>{t('settings.systemTheme')}</DropdownMenu.ItemTitle>
                        </DropdownMenu.Item>
                    </DropdownMenu.Content>
                </DropdownMenu.Root>
            </View>
        </View>
    )
}

export default AppearanceSetting