import { useColorScheme } from "@hooks/useColorScheme"
import { LegendList } from "@legendapp/list"
import { Message } from "@raven/types/common/Message"
import { useLocalSearchParams } from "expo-router"
import { useFrappeGetCall } from "frappe-react-sdk"
import { View } from "react-native"
import { Text } from '@components/nativewindui/Text';
import PinnedMessageItem from "./PinnedMessageItem"
import ErrorBanner from "@components/common/ErrorBanner"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

const PinnedMessageList = () => {

    const { id } = useLocalSearchParams()
    const { colors } = useColorScheme()
    const { data, error } = useFrappeGetCall<{ message: Message[] }>("raven.api.raven_message.get_pinned_messages", { 'channel_id': id }, undefined, {
        revalidateOnFocus: false
    })

    if (error) {
        return (
            <View className="p-4">
                <ErrorBanner error={error} />
            </View>
        )
    }

    return (
        <LegendList
            data={data?.message ?? []}
            ListEmptyComponent={<PinnedMessagesEmptyState />}
            renderItem={({ item }) => <PinnedMessageItem message={item} />}
            keyExtractor={(item) => item.name}
            estimatedItemSize={100}
            contentContainerStyle={{ paddingTop: 8, paddingBottom: 32, backgroundColor: colors.background }}
        />
    )
}

const PinnedMessagesEmptyState = () => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    return (
        <View className="flex-1 justify-center items-center p-4">
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <Text className="text-muted-foreground">{t('messages.noPinnedMessages')}</Text>
        </View>
    )
}
export default PinnedMessageList