import { useContext, useEffect, useRef } from 'react'
//// Neoffice - Platform, to tag the token with its OS in the Mobile Device registry (857cd52ad + c6d819541, 2026-01-04).
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
        //// Neoffice - push registration tracing (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").
        //// TO REVIEW: left in from the debugging pass, runs on every app start.
        console.log('[PushToken] Hook triggered, siteInfo:', siteInfo?.sitename, 'callMade:', callMade.current)

        if (callMade.current) return
        callMade.current = true

        // When the site is switched, fetch the token and store it in the database
        if (siteInfo) {
            //// Neoffice - push registration tracing (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"). TO REVIEW: debugging leftover.
            console.log('[PushToken] Requesting permission...')
            messaging.requestPermission().then(async (authorizationStatus) => {
                //// Neoffice - push registration tracing (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"). TO REVIEW: debugging leftover.
                console.log('[PushToken] Permission status:', authorizationStatus)
                if (authorizationStatus === AuthorizationStatus.AUTHORIZED) {
                    //// Neoffice - FCM tokens go to neoffice_theme's Mobile Device registry (857cd52ad + c6d819541, 2026-01-04
                    //// "Register FCM tokens with neoffice_theme Mobile Device" + "Pass app='synk'"). Upstream posts
                    //// the token to raven.api.notification.subscribe only, i.e. to Raven Cloud, which we do not use:
                    //// our pushes are sent from the instance through the Firebase App Configuration named 'synk'.
                    //// The Raven call is kept for backward compatibility but is not allowed to fail the registration.
                    //// TO REVIEW: the console.log lines print the first 30 characters of the FCM token.
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
            //// Neoffice - a rejected permission request used to end in an unhandled rejection (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle").
            }).catch((error) => {
                console.error('[PushToken] Permission request error:', error)
            })
        //// Neoffice - push registration tracing (b30ad1930, 2026-01-05 "fix(mobile): Android push notifications and notification toggle"). TO REVIEW: debugging leftover.
        } else {
            console.log('[PushToken] No siteInfo, skipping')
        }

    }, [siteInfo])
}

export default useFirebasePushTokenListener