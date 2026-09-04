//// Neoffice - Platform, to tell the neoffice_theme Mobile Device registry which OS the token
//// belongs to (857cd52ad + c6d819541, 2026-01-04).
import { Platform, View } from 'react-native'
import BellOutlineIcon from '@assets/icons/BellOutlineIcon.svg'
import { useColorScheme } from '@hooks/useColorScheme'
import { Text } from '@components/nativewindui/Text'
import { Toggle } from '@components/nativewindui/Toggle'
import { useCallback, useContext, useEffect, useState } from 'react'
import { AuthorizationStatus, getMessaging } from '@react-native-firebase/messaging';
import { FrappeConfig, FrappeContext } from 'frappe-react-sdk'
import { toast } from 'sonner-native'
import * as Device from 'expo-device';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const messaging = getMessaging()

const NotificationSetting = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const { colors } = useColorScheme()
    const [enabled, setEnabled] = useState(false)

    const { call } = useContext(FrappeContext) as FrappeConfig

    useEffect(() => {
        messaging.hasPermission().then((hasPermission) => {
            setEnabled(hasPermission === AuthorizationStatus.AUTHORIZED)
        })
    }, [])

    //// Neoffice - push notifications rewired (857cd52ad + c6d819541, 2026-01-04 + b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").
    //// Upstream requests permission first and only then fetches a token, inside nested .then() chains;
    //// on Android that ordering left the toggle stuck on when getToken() failed after permission was
    //// granted. Rewritten as async/await with a single try/catch, token first.
    const onToggle = useCallback(async (newValue: boolean) => {
        try {
            const token = await messaging.getToken()
            if (!token) {
                toast.error(t('errors.somethingWentWrong'))
                return
            }

            if (newValue) {
                const authorizationStatus = await messaging.requestPermission()

                if (authorizationStatus !== AuthorizationStatus.AUTHORIZED && authorizationStatus !== AuthorizationStatus.EPHEMERAL) {
                    //// Neoffice - the token is registered with neoffice_theme's Mobile Device registry
                    //// (857cd52ad + c6d819541, 2026-01-04), which is what actually sends our pushes: one token store for the whole
                    //// fleet, keyed by app='synk'. raven.api.notification.subscribe is still called after it, but
                    //// tolerated failing - Raven Cloud is not our delivery path.
                    toast.error(t('errors.somethingWentWrong'))
                    return
                }

                // Register with neoffice_theme Mobile Device (primary system)
                await call.post('neoffice_theme.mobile.register_device_token', {
                    token: token,
                    platform: Platform.OS === 'ios' ? 'ios' : 'android',
                    device_id: Device.deviceName || 'Synk-Mobile',
                    app: 'synk'
                })

                // Also register with Raven for backward compatibility
                try {
                    await call.post('raven.api.notification.subscribe', {
                        fcm_token: token,
                        environment: 'Mobile',
                        device_information: Device.deviceName
                    })
                } catch (e) {
                    // Raven subscribe is optional
                }
                //// Neoffice - end of the nested-.then() block replaced by the async/await above (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").

                //// Neoffice - disabling now unregisters from the Mobile Device registry first (857cd52ad + c6d819541, 2026-01-04).
                setEnabled(true)
            } else {
                // Deactivate Mobile Device
                await call.post('neoffice_theme.mobile.unregister_device_token', {
                    token: token
                })
                //// Neoffice - Raven Cloud unsubscribe kept for backward compatibility, but not fatal (857cd52ad + c6d819541, 2026-01-04).

                // Also unsubscribe from Raven
                try {
                    await call.post('raven.api.notification.unsubscribe', {
                        fcm_token: token
                    })
                //// Neoffice - swallow the Raven Cloud failure: an instance that never used Raven Cloud has no
                //// subscription to remove (857cd52ad + c6d819541, 2026-01-04).
                } catch (e) {
                    // Raven unsubscribe is optional
                }
                //// Neoffice - tail of the replaced .then() chain (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").

                //// Neoffice - single failure path for the whole toggle, with a translated message (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").
                setEnabled(false)
            }
        } catch (error) {
            toast.error(t('errors.somethingWentWrong'))
        }
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t added to the deps so it recomputes on a language switch.
    }, [t, call])

    return (
        <View>
            <View className='flex flex-row py-2.5 px-4 rounded-xl justify-between bg-background dark:bg-card'>
                <View className='flex-row items-center gap-2'>
                    <BellOutlineIcon height={18} width={18} fill={colors.icon} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base'>{t('notifications.pushNotifications')}</Text>
                </View>
                <Toggle value={enabled} onValueChange={onToggle} />
            </View>
        </View>
    )
}

export default NotificationSetting