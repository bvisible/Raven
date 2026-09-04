import useCurrentRavenUser from "@raven/lib/hooks/useCurrentRavenUser"
import { useMemo, useState } from "react"
import { View, TouchableOpacity, StyleSheet } from "react-native"
import { useColorScheme } from "@hooks/useColorScheme"
import { ChannelListItem } from "@raven/types/common/ChannelListItem"
import { ChannelListRow } from "../ChannelList/ChannelListRow"
import ChevronDownIcon from '@assets/icons/ChevronDownIcon.svg'
import ChevronRightIcon from '@assets/icons/ChevronRightIcon.svg'
import { Text } from '@components/nativewindui/Text';
import { Divider } from "@components/layout/Divider"
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const PinnedChannelsList = ({ channels }: { channels: ChannelListItem[] }) => {

    const { myProfile } = useCurrentRavenUser()

    // Filter channels that are pinned from the list of read channels
    const pinnedChannels = useMemo(() => {
        if (myProfile) {
            const pinnedChannelIDs = myProfile.pinned_channels?.map(pin => pin.channel_id)
            return channels.filter(channel => pinnedChannelIDs?.includes(channel.name))
        } else {
            return []
        }
    }, [channels, myProfile])

    if (pinnedChannels.length === 0) {
        return null
    }

    return (
        <>
            <PinnedChannelListUI channels={pinnedChannels} />
            <Divider prominent />
        </>
    )
}

export default PinnedChannelsList

const PinnedChannelListUI = ({ channels }: { channels: ChannelListItem[] }) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation();
    const [isExpanded, setIsExpanded] = useState(true)
    const { colors } = useColorScheme()

    const toggleAccordion = () => {
        setIsExpanded((prev) => !prev)
    }

    return (
        <View style={styles.container}>
            <TouchableOpacity onPress={toggleAccordion} style={styles.header} activeOpacity={0.7}>
                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                <Text style={styles.headerText}>{t('channels.pinnedChannels')}</Text>
                {isExpanded ? <ChevronDownIcon fill={colors.icon} /> : <ChevronRightIcon fill={colors.icon} />}
            </TouchableOpacity>
            {isExpanded && <>
                {channels.map((channel) => <ChannelListRow key={channel.name} channel={channel} />)}
            </>}
        </View>
    )
}

const styles = StyleSheet.create({
    container: {
        padding: 10,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 12,
        paddingHorizontal: 10,
    },
    headerText: {
        fontWeight: '600',
        fontSize: 16,
    }
})