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
import { useTranslation } from 'react-i18next';

const messaging = getMessaging()

const NotificationSetting = () => {
    const { t } = useTranslation();
    const { colors } = useColorScheme()
    const [enabled, setEnabled] = useState(false)

    const { call } = useContext(FrappeContext) as FrappeConfig

    useEffect(() => {
        messaging.hasPermission().then((hasPermission) => {
            setEnabled(hasPermission === AuthorizationStatus.AUTHORIZED)
        })
    }, [])

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

                setEnabled(true)
            } else {
                // Deactivate Mobile Device
                await call.post('neoffice_theme.mobile.unregister_device_token', {
                    token: token
                })

                // Also unsubscribe from Raven
                try {
                    await call.post('raven.api.notification.unsubscribe', {
                        fcm_token: token
                    })
                } catch (e) {
                    // Raven unsubscribe is optional
                }

                setEnabled(false)
            }
        } catch (error) {
            toast.error(t('errors.somethingWentWrong'))
        }
    }, [t, call])

    return (
        <View>
            <View className='flex flex-row py-2.5 px-4 rounded-xl justify-between bg-background dark:bg-card'>
                <View className='flex-row items-center gap-2'>
                    <BellOutlineIcon height={18} width={18} fill={colors.icon} />
                    <Text className='text-base'>{t('notifications.pushNotifications')}</Text>
                </View>
                <Toggle value={enabled} onValueChange={onToggle} />
            </View>
        </View>
    )
}

export default NotificationSetting