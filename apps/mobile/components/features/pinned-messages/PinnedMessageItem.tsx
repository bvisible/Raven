import { Message } from "@raven/types/common/Message"
import { View } from "react-native"
import { Text } from '@components/nativewindui/Text'
import { formatDateAndTime } from "@raven/lib/utils/dateConversions"
import { BaseMessageItem } from "../chat-stream/BaseMessageItem"
import * as ContextMenu from 'zeego/context-menu';
import { useColorScheme } from "@hooks/useColorScheme";
import { useTogglePinMessage } from "@hooks/useTogglePinMessage"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next"

const PinnedMessageItem = ({ message }: { message: Message }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const { TogglePin } = useTogglePinMessage({ ...message, is_pinned: 1 })

    return (
        <ContextMenu.Root>
            <ContextMenu.Trigger>
                <View>
                    <View className='flex flex-row items-center px-3 pt-2 gap-2'>
                        <Text className='text-[13px] text-muted-foreground'>
                            {formatDateAndTime(message.creation)}
                        </Text>
                    </View>
                    <BaseMessageItem message={message} />
                </View>
            </ContextMenu.Trigger>
            <ContextMenu.Content>
                <ContextMenu.Item key="unpin" onSelect={TogglePin}>
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <ContextMenu.ItemTitle>{t('messages.unpinMessage')}</ContextMenu.ItemTitle>
                    <ContextMenu.ItemIcon
                        ios={{
                            name: 'pin.slash',
                            pointSize: 14,
                            weight: 'semibold',
                            scale: 'medium',
                            // can also be a color string. Requires iOS 15+
                            hierarchicalColor: {
                                dark: colors.icon,
                                light: colors.icon,
                            },
                            // alternative to hierarchical color. Requires iOS 15+
                            paletteColors: [
                                {
                                    dark: colors.icon,
                                    light: colors.icon,
                                },
                            ],
                        }}
                    />
                </ContextMenu.Item>
            </ContextMenu.Content>
        </ContextMenu.Root>
    )
}

export default PinnedMessageItem