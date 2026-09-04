import { Pressable, View } from 'react-native';
import Animated, { LayoutAnimationConfig, ZoomInRotate } from 'react-native-reanimated';
import * as DropdownMenu from 'zeego/dropdown-menu'
import { cn } from '@lib/cn';
import { useColorScheme } from '@hooks/useColorScheme';
import { COLORS } from '@theme/colors';
import SunIcon from '@assets/icons/SunIcon.svg';
import MoonIcon from '@assets/icons/MoonIcon.svg';
import SunMoonIcon from '@assets/icons/SunMoonIcon.svg';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export function ThemeToggle() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const { setColorScheme, themeValue } = useColorScheme();

    return (
        <DropdownMenu.Root>
            <DropdownMenu.Trigger>
                <LayoutAnimationConfig skipEntering>
                    <Animated.View
                        className="items-center justify-center"
                        key={"toggle-" + themeValue}
                        entering={ZoomInRotate}>
                        <Pressable
                            hitSlop={10}
                            className="opacity-80">
                            {themeValue === 'dark'
                                ? ({ pressed }) => (
                                    <View className={cn('px-0.5', pressed && 'opacity-50')}>
                                        <MoonIcon color={COLORS.white} width={20} height={20} />
                                    </View>
                                )
                                : themeValue === 'system'
                                    ? ({ pressed }) => (
                                        <View className={cn('px-0.5', pressed && 'opacity-50')}>
                                            <SunMoonIcon color={COLORS.white} width={20} height={20} />
                                        </View>
                                    )
                                    : ({ pressed }) => (
                                        <View className={cn('px-0.5', pressed && 'opacity-50')}>
                                            <SunIcon color={COLORS.white} width={20} height={20} />
                                        </View>
                                    )}
                        </Pressable>
                    </Animated.View>
                </LayoutAnimationConfig>
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
    );
}