import { Button } from "@components/nativewindui/Button";
import { Text } from "@components/nativewindui/Text";
import { useColorScheme } from "@hooks/useColorScheme";
import { Link, Stack } from "expo-router";
import CrossIcon from '@assets/icons/CrossIcon.svg';
import { Platform, View } from "react-native";
import PinnedMessageList from "@components/features/pinned-messages/PinnedMessageList";
import PinOutlineIcon from "@assets/icons/PinOutlineIcon.svg";
import CommonErrorBoundary from "@components/common/CommonErrorBoundary";
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next";

const PinnedMessages = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    return (
        <>
            <Stack.Screen
                options={{
                    headerStyle: { backgroundColor: colors.background },
                    headerLeft: Platform.OS === 'ios' ? () => {
                        return (
                            <Link asChild href="../" relativeToDirectory>
                                <Button variant="plain" className="ios:px-0" hitSlop={10}>
                                    <CrossIcon color={colors.icon} height={24} width={24} />
                                </Button>
                            </Link>
                        )
                    } : undefined,
                    headerTitle: () => (
                        <View className='flex-row items-center'>
                            <PinOutlineIcon height={18} width={18} stroke={colors.foreground} />
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <Text className='ml-2 text-base font-semibold'>{t('messages.pinnedMessages')}</Text>
                        </View>
                    ),
                }} />
            <PinnedMessageList />
        </>
    )
}

export default PinnedMessages;


export const ErrorBoundary = CommonErrorBoundary