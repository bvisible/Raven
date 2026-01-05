import { useContext, useEffect, useRef } from 'react'
import { Platform } from 'react-native'
import * as Device from 'expo-device';
import { AuthorizationStatus, getMessaging } from '@react-native-firebase/messaging';
import useSiteContext from './useSiteContext';
import { FrappeConfig, FrappeContext } from 'frappe-react-sdk';

const messaging = getMessaging()

const useFirebasePushTokenListener = () => {

    const siteInfo = useSiteContext()

    const { call } = useContext(FrappeContext) as FrappeConfig

    const callMade = useRef(false)

    useEffect(() => {
        console.log('[PushToken] Hook triggered, siteInfo:', siteInfo?.sitename, 'callMade:', callMade.current)

        if (callMade.current) return
        callMade.current = true

        // When the site is switched, fetch the token and store it in the database
        if (siteInfo) {
            console.log('[PushToken] Requesting permission...')
            messaging.requestPermission().then(async (authorizationStatus) => {
                console.log('[PushToken] Permission status:', authorizationStatus)
                if (authorizationStatus === AuthorizationStatus.AUTHORIZED) {
                    try {
                        const token = await messaging.getToken()
                        console.log('[PushToken] Got FCM token:', token?.substring(0, 30) + '...')

                        // Register with neoffice_theme Mobile Device (unified token store)
                        const response = await call.post('neoffice_theme.mobile.register_device_token', {
                            token: token,
                            platform: Platform.OS === 'ios' ? 'ios' : 'android',
                            device_id: Device.deviceName || 'Synk-Mobile',
                            app: 'synk'  // Link to Firebase App Configuration
                        })
                        console.log('[PushToken] Mobile Device register response:', response)

                        // Also register with Raven for backward compatibility
                        try {
                            await call.post('raven.api.notification.subscribe', {
                                fcm_token: token,
                                environment: 'Mobile',
                                device_information: Device.deviceName
                            })
                            console.log('[PushToken] Raven subscribe done')
                        } catch (ravenError) {
                            console.log('[PushToken] Raven subscribe skipped:', ravenError)
                        }
                    } catch (error) {
                        console.error('[PushToken] Error:', error)
                    }
                } else {
                    console.log('[PushToken] Permission NOT authorized')
                }
            }).catch((error) => {
                console.error('[PushToken] Permission request error:', error)
            })
        } else {
            console.log('[PushToken] No siteInfo, skipping')
        }

    }, [siteInfo])
}

export default useFirebasePushTokenListener