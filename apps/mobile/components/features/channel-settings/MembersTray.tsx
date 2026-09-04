import UserAvatar from "@components/layout/UserAvatar";
import { View } from "react-native";
import { Text } from "@components/nativewindui/Text";
import { useLocalSearchParams } from "expo-router";
import { useFetchChannelMembers } from "@raven/lib/hooks/useFetchChannelMembers";
import { ScrollView } from "react-native-gesture-handler";
import { Button } from "@components/nativewindui/Button";
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next";
interface MembersTrayProps {
    onViewAll: () => void
}

export const MembersTray = ({ onViewAll }: MembersTrayProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { id: channelId } = useLocalSearchParams()
    const { channelMembers } = useFetchChannelMembers(channelId as string ?? "")

    const displayMembers = Object.values(channelMembers).slice(0, 10)
    const membersCount = channelMembers ? Object.keys(channelMembers).length : 0

    // Helper function to split the full name into first name and the rest
    const splitName = (fullName: string) => {
        const names = fullName.split(" ")
        const firstName = names[0]
        const restOfName = names.slice(1).join(" ")
        return { firstName, restOfName }
    }

    return (
        <View className="flex-col px-4 gap-3">
            <View className="flex-row items-center justify-between">
                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                <Text className="text-[15px] font-medium">{t('common.members')} ({membersCount})</Text>
                <Button variant="plain" size="none" onPress={onViewAll}>
                    <View className="flex-row items-center justify-end">
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className="text-[15px] font-medium text-primary dark:text-secondary">{t('common.viewAll')}</Text>
                    </View>
                </Button>
            </View>
            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerClassName="flex-row gap-2"
            >
                {displayMembers.map((member, index) => {
                    const { firstName, restOfName } = splitName(member.full_name ?? "");

                    return (
                        <View className="flex-col gap-1 items-center" key={index}>
                            <UserAvatar
                                src={member.user_image ?? ""}
                                alt={member.full_name ?? ""}
                                availabilityStatus={member.availability_status}
                                avatarProps={{ className: "w-14 h-14" }}
                            />
                            <View className="flex-col gap-0.5">
                                <Text className="text-sm text-center pt-1.5">
                                    {firstName}
                                </Text>
                                <Text className="text-sm text-center" numberOfLines={1}>
                                    {restOfName}
                                </Text>
                            </View>
                        </View>
                    )
                })}
            </ScrollView>
        </View>
    )
}