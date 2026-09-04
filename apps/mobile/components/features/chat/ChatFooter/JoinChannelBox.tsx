import { useFrappeCreateDoc, useSWRConfig } from "frappe-react-sdk"
import { Button } from "@components/nativewindui/Button"
import ErrorBanner from "@components/common/ErrorBanner"
import { Text } from "@components/nativewindui/Text"
import { View } from "react-native"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

interface JoinChannelBoxProps {
    channelID: string,
    isThread: boolean,
    user: string,
}

export const JoinChannelBox = ({ channelID, isThread, user }: JoinChannelBoxProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { mutate } = useSWRConfig()

    const { createDoc, error, loading } = useFrappeCreateDoc()

    const joinChannel = async () => {
        return createDoc('Raven Channel Member', {
            channel_id: channelID,
            user_id: user
        }).then(() => {
            mutate(["channel_members", channelID])
        })
    }

    return (
        <View className="flex-col gap-2 items-center border-t border-l border-r border-border rounded-2xl px-4 py-4">
            {error && <ErrorBanner error={error} />}
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="text-sm text-muted-foreground">{isThread ? t('channels.notThreadMember') : t('channels.notMember')}</Text>
            <Button
                onPress={joinChannel}
                size="md"
                variant="primary"
                className="w-full rounded-lg"
                disabled={loading}
            >
                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                {loading ? <Text className="gap-1 text-center w-full font-semibold text-base">{t('channels.joining')}</Text> :
                    <Text className="gap-1 text-center w-full font-semibold text-base">{t('channels.join')}</Text>}
            </Button>
        </View>
    )
}