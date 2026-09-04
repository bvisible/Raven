import { useFrappeUpdateDoc, useSWRConfig } from "frappe-react-sdk"
import { toast } from "sonner-native"
import { Text } from "@components/nativewindui/Text"
import { View } from "react-native"
import { Button } from "@components/nativewindui/Button"
import ErrorBanner from "@components/common/ErrorBanner"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface ArchivedChannelBoxProps {
    channelID: string,
    isMemberAdmin?: 0 | 1
}

export const ArchivedChannelBox = ({ channelID, isMemberAdmin }: ArchivedChannelBoxProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    return (
        <View className="flex-col gap-2 items-center border-t border-l border-r border-border rounded-2xl px-4 py-4">
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="text-sm text-muted-foreground">{t('channels.channelArchived')}</Text>
            {isMemberAdmin === 1 ? <UnArchiveButton channelID={channelID} /> : null}
        </View>
    )
}

const UnArchiveButton = ({ channelID }: { channelID: string }) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { updateDoc, loading, error } = useFrappeUpdateDoc()
    const { mutate } = useSWRConfig()

    const unArchiveChannel = async () => {
        return updateDoc('Raven Channel', channelID, {
            is_archived: 0
        }).then(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('channels.channelRestored'))
            mutate("channel_list")
        }).catch(err => {
            toast.error(err.message)
        })
    }

    if (error) {
        return <ErrorBanner error={error} />
    }

    return (
        <Button
            onPress={unArchiveChannel}
            size='md'
            variant="tonal"
            className="w-full rounded-full"
            disabled={loading}
        >
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            {loading ? <Text className="gap-1 text-center w-full font-semibold text-base">{t('common.restoring')}</Text> : <Text className="gap-1 text-center w-full font-semibold text-base">{t('channels.restoreChannel')}</Text>}
        </Button>
    )
}