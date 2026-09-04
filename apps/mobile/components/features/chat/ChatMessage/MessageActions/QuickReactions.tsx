import { Pressable, View } from 'react-native'
import SmilePlus from "@assets/icons/SmilePlus.svg"
import { Text } from '@components/nativewindui/Text'
import { Message } from '@raven/types/common/Message'
import { useColorScheme } from '@hooks/useColorScheme'
import { Sheet, useSheetRef } from '@components/nativewindui/Sheet'
import { BottomSheetView } from '@gorhom/bottom-sheet'
import EmojiPicker from '@components/common/EmojiPicker/EmojiPicker'
import { toast } from 'sonner-native'
import useReactToMessage from '@raven/lib/hooks/useReactToMessage'
import { Emoji } from '@components/common/EmojiPicker/Picker'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

interface MessageReactionsProps {
    message: Message | null
    onClose: () => void
    quickReactionEmojis: string[]
}

const QuickReactions = ({ message, onClose, quickReactionEmojis }: MessageReactionsProps) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const emojiBottomSheetRef = useSheetRef()

    const saveReaction = useReactToMessage()

    const onReactNatively = (emoji: string) => {
        if (message) {
            saveReaction(message, emoji).then(() => {
                emojiBottomSheetRef.current?.close({ duration: 450 })
                onClose();
            }).catch(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.error(t('messages.reactionFailed'))
            })
        }
    }

    const onReactEmoji = (emoji: Emoji) => {

        if (message) {
            if (emoji.native) {
                saveReaction(message, emoji.native)
                    .then(() => {
                        emojiBottomSheetRef.current?.close({ duration: 450 })
                        onClose();
                    }).catch(() => {
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                        toast.error(t('messages.reactionFailed'))
                    })
            } else {
                saveReaction(message, emoji?.src ?? "", true, emoji.id)
                    .then(() => {
                        emojiBottomSheetRef.current?.close({ duration: 450 })
                        onClose();
                    }).catch(() => {
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                        toast.error(t('messages.reactionFailed'))
                    })
            }
        }

    }

    return (
        <>
            <View className="flex flex-row justify-between">
                {quickReactionEmojis.map((reaction) => (
                    <Pressable
                        key={reaction}
                        hitSlop={10}
                        onPress={() => onReactNatively(reaction)}
                        className='w-12 h-12 items-center justify-center bg-card rounded-full active:scale-90 transition-all duration-100 active:bg-card/70 active:border active:border-border/30'>
                        <Text className="text-lg">{reaction}</Text>
                    </Pressable>
                ))}
                <Pressable
                    className='w-12 h-12 items-center justify-center bg-card rounded-full active:scale-90 transition-all duration-100 active:bg-card/70 active:border active:border-border/30'
                    onPress={() => emojiBottomSheetRef.current?.present()}>
                    <SmilePlus width={24} height={24} color={colors.icon} />
                </Pressable>
            </View>

            <Sheet ref={emojiBottomSheetRef} enableDynamicSizing={false} snapPoints={["65"]}>
                <BottomSheetView className='flex-1'>
                    <EmojiPicker onReact={onReactEmoji} />
                </BottomSheetView>
            </Sheet>
        </>
    )
}

export default QuickReactions