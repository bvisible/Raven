import { useCallback, useContext } from 'react';
import { CustomTextualRenderer, CustomRendererProps, TText, TPhrasing } from 'react-native-render-html';
import { router } from 'expo-router'
import { FrappeContext, FrappeConfig } from 'frappe-react-sdk';
import { toast } from 'sonner-native';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

// Custom renderer for paragraph elements, it also checks for mentions
export const CustomMentionRenderer: CustomTextualRenderer = ({
    TDefaultRenderer,
    ...props
}) => {

    const attributes = props.tnode.attributes

    if (attributes?.['data-type'] === 'userMention') {
        return <UserMentionRenderer userID={attributes?.['data-id']} TDefaultRenderer={TDefaultRenderer} {...props} />
    }

    if (attributes?.['data-type'] === 'channelMention') {

        return <ChannelMentionRenderer channelID={attributes?.['data-id']} TDefaultRenderer={TDefaultRenderer} {...props} />
    }

    // @ts-ignore
    return <TDefaultRenderer {...props} />

}

const UserMentionRenderer = ({
    userID,
    TDefaultRenderer,
    ...props
}: CustomRendererProps<TText | TPhrasing> & { userID: string }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { call } = useContext(FrappeContext) as FrappeConfig

    const handleMentionPress = useCallback(() => {
        call.post('raven.api.raven_channel.create_direct_message_channel', {
            user_id: userID
        }).then((res) => {
            router.push(`../${res?.message}`, { relativeToDirectory: true })
        }).catch(err => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('directMessages.createDMFailed'))
        })
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t added to the deps so it recomputes on a language switch.
    }, [userID, t])

    return (
        // @ts-ignore
        <TDefaultRenderer {...props} onPress={handleMentionPress} />
    );
}

const ChannelMentionRenderer = ({
    channelID,
    TDefaultRenderer,
    ...props
}: CustomRendererProps<TText | TPhrasing> & { channelID: string }) => {

    const handleMentionPress = useCallback(() => {
        router.push(`../${channelID}`, { relativeToDirectory: true })
    }, [channelID])

    // @ts-ignore
    return <TDefaultRenderer {...props} onPress={handleMentionPress} />
}