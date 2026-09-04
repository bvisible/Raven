import { FrappeConfig, FrappeContext, useSWR } from "frappe-react-sdk"
import { useContext, useRef } from "react"
import { toast } from "sonner-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

// Check the socket connection every 2 minutes if the user focuses back on the page
export const useActiveSocketConnection = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { socket } = useContext(FrappeContext) as FrappeConfig

    const socketConnectionCount = useRef(0)

    const { data } = useSWR('socket_test', () => {
        return socket?.connected ? true : Promise.reject(new Error('Socket not connected'))
    }, {

        onSuccess: () => {
            socketConnectionCount.current = 0
        },
        onError: (error) => {
            // If the socket connection fails more than 2 times, then show an error message
            if (socketConnectionCount.current === 2) {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('errors.realtimeNotWorking'), {
                    duration: 5000
                })
            } else {
                // Else try to connect to socket
                socket?.connect()
                socketConnectionCount.current += 1
            }

        },
        errorRetryCount: 3,
    })

    return data
}