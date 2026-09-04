import { router } from 'expo-router';
import { FrappeConfig, FrappeContext } from 'frappe-react-sdk';
import { revokeAsync } from 'expo-auth-session';
import { useContext } from 'react';
import { clearDefaultSite, deleteAccessToken, getRevocationEndpoint } from '@lib/auth';
import { toast } from 'sonner-native';
import { useSetAtom } from 'jotai';
import { selectedWorkspaceFamily } from './useGetCurrentWorkspace';
import useSiteContext from './useSiteContext';
import { getMessaging } from '@react-native-firebase/messaging';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const messaging = getMessaging()


export const useLogout = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const siteInformation = useSiteContext()
    const { tokenParams, call } = useContext(FrappeContext) as FrappeConfig

    const setSelectedWorkspace = useSetAtom(selectedWorkspaceFamily(siteInformation?.sitename || ''))

    const logout = () => {
        // Remove the current site from AsyncStorage
        // Revoke the token
        // Redirect to the landing page
        try {
            messaging.getToken().then((token) => {
                if (token) {
                    call.post('raven.api.notification.unsubscribe', {
                        fcm_token: token
                    })
                }
            })
        } catch (error) {
            console.error(error)
        }
        setSelectedWorkspace('')
        clearDefaultSite()
            .then(() => {
                router.replace('/landing')
            })
            .then(() => {
                return deleteAccessToken(siteInformation?.sitename || '')
            })
            .catch((error) => {
                console.error(error)
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('auth.logoutFailed'))
            })
            .then(() => {
                revokeAsync({
                    clientId: siteInformation?.client_id || '',
                    token: tokenParams?.token?.() || ''
                }, {
                    revocationEndpoint: getRevocationEndpoint(siteInformation?.url || '')
                })
            })
    }

    return logout


}