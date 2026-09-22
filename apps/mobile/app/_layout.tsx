import 'expo-dev-client';
import { router, Slot } from 'expo-router';
import { ThemeProvider } from '@react-navigation/native';
import "../global.css";
import { useEffect, useState } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { BottomSheetModalProvider } from '@gorhom/bottom-sheet';
import { setNavigationBar, themeAtom } from '@hooks/useColorScheme';
import { NAV_THEME } from '@theme/index';
import { StatusBar } from 'expo-status-bar';
import { ActionSheetProvider } from '@expo/react-native-action-sheet';
import { PortalHost } from '@rn-primitives/portal';
import { KeyboardProvider } from 'react-native-keyboard-controller';
import { useAsyncStorage } from '@react-native-async-storage/async-storage';
import { Toaster } from 'sonner-native';
import { LogBox, Platform } from 'react-native';
import { getMessaging } from '@react-native-firebase/messaging';
import { setDefaultSite } from '@lib/auth';
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import advancedFormat from 'dayjs/plugin/advancedFormat'
import relativeTime from 'dayjs/plugin/relativeTime';
import { useAtom } from 'jotai';
import { useColorScheme } from 'nativewind';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import '@lib/i18n';
import { loadSavedLanguage } from '@lib/i18n';
import * as SplashScreen from 'expo-splash-screen';
import * as SystemUI from 'expo-system-ui';
import { Appearance } from 'react-native';

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(advancedFormat)
dayjs.extend(relativeTime)

/** Suppressing this for now - see https://github.com/meliorence/react-native-render-html/issues/661 */
LogBox.ignoreLogs([
    /Support for defaultProps will be removed/,
]);

if (__DEV__) {
    LogBox.ignoreLogs([
        /Support for defaultProps will be removed/,
    ]);
}

// Prevent splash from auto-hiding before app is ready
SplashScreen.preventAutoHideAsync()

SplashScreen.setOptions({
    duration: 200,
    fade: true,
});

const messaging = getMessaging()

export default function RootLayout() {


    const [appIsReady, setAppIsReady] = useState(false);
    const { getItem } = useAsyncStorage(`default-site`);
    const { colorScheme, setColorScheme } = useColorScheme();
    const isDarkColorScheme = colorScheme === 'dark';
    const [theme] = useAtom(themeAtom);

    // Set system UI background color early to prevent flash
    useEffect(() => {
        const setSystemBackground = async () => {
            const scheme = Appearance.getColorScheme();
            const bgColor = scheme === 'dark' ? '#121212' : '#ffffff';
            await SystemUI.setBackgroundColorAsync(bgColor);
        };
        setSystemBackground();
    }, []);


    useEffect(() => {

        const onMount = async () => {

            try {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): restore the saved language before the
                //// first screen renders, otherwise the app flashes the device locale then switches.
                await loadSavedLanguage();

                // Get the defualt site from the async storage
                // Also check if the app was started by a notification
                const initialNotification = await messaging.getInitialNotification();

                if (initialNotification) {
                    if (initialNotification.data?.channel_id && initialNotification.data?.sitename) {
                        setDefaultSite(initialNotification.data.sitename as string)
                        let path = 'chat'
                        if (initialNotification.data.is_thread) {
                            path = 'thread'
                        }
                        router.navigate(`/${initialNotification.data.sitename}/${path}/${initialNotification.data.channel_id}`, {
                            withAnchor: true
                        })

                        return
                    }
                }

                // If not started by notification
                // On load, check if the user has a site set
                const defaultSite = await getItem()
                if (defaultSite) {
                    router.replace(`/${defaultSite}`)
                } else {
                    router.replace('/landing')
                }

            } catch (error) {
                console.warn('Error during app initialization:', error);
                router.replace('/landing');
            } finally {
                // mark app as ready regardless of success or failure
                setAppIsReady(true);
            }

        }

        // Handle notification open when app is in background
        const unsubscribeOnNotificationOpen = messaging.onNotificationOpenedApp(async (remoteMessage) => {
            //// Neoffice - push-notification deep links (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"): upstream leaves this line commented
            //// out; re-enabled behind __DEV__ on 2026-09-04 instead of always on.
            if (__DEV__) console.log('[Notification] App opened from background:', JSON.stringify(remoteMessage.data));
            if (remoteMessage.data?.channel_id && remoteMessage.data?.sitename) {
                //// Neoffice - push-notification deep links (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"): same route construction for the
                //// background case; here is_thread arrives as the string '1', not a number.
                const targetPath = `/${remoteMessage.data.sitename}/${remoteMessage.data.is_thread === '1' ? 'thread' : 'chat'}/${remoteMessage.data.channel_id}`;
                //// Neoffice - __DEV__ only (2026-09-04), see above.
                if (__DEV__) console.log('[Notification] Navigating to:', targetPath);
                setDefaultSite(remoteMessage.data.sitename as string)
                let path = 'chat'
                if (remoteMessage.data.is_thread === '1') {
                    path = 'thread'
                }
                router.navigate(`/${remoteMessage.data.sitename}/${path}/${remoteMessage.data.channel_id}`, {
                    withAnchor: true
                })
            //// Neoffice - push-notification deep links (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"). __DEV__ only (2026-09-04).
            } else {
                if (__DEV__) console.log('[Notification] Missing channel_id or sitename in notification data');
            }
        });

        onMount()
        // Cleanup function
        return () => {
            unsubscribeOnNotificationOpen();
        };
    }, []);

    // Hide splash screen when app is ready
    useEffect(() => {
        if (appIsReady) {
            SplashScreen.hide();
        }
    }, [appIsReady]);

    useEffect(() => {
        if (theme.state === 'hasData') {
            if (theme.data) {
                setColorScheme(theme.data);
            }
        }
    }, [theme]);

    useEffect(() => {
        if (Platform.OS !== 'android' || !colorScheme) return;
        try {
            setNavigationBar(colorScheme)
        } catch (error) {
            console.error('useColorScheme.tsx", "setColorScheme', error);
        }
    }, [colorScheme])

    return (
        <>
            <StatusBar
                key={`root-status-bar-${isDarkColorScheme ? 'light' : 'dark'}`}
                style={isDarkColorScheme ? 'light' : 'dark'}
            />
            <GestureHandlerRootView style={{ flex: 1 }}>
                <BottomSheetModalProvider>
                    <ActionSheetProvider>
                        <KeyboardProvider statusBarTranslucent navigationBarTranslucent>
                            <ThemeProvider value={NAV_THEME[colorScheme ?? 'light']}>
                                <Slot />
                                <PortalHost />
                            </ThemeProvider>
                        </KeyboardProvider>
                    </ActionSheetProvider>
                </BottomSheetModalProvider>
                <Toaster
                    position="top-center"
                    duration={2000}
                    visibleToasts={4}
                    closeButton={true}
                    toastOptions={{}}
                    pauseWhenPageIsHidden
                    theme={isDarkColorScheme ? 'dark' : 'light'}
                    swipeToDismissDirection='up'
                />
            </GestureHandlerRootView>
        </>
    )
}
