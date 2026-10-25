//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import { useMemo } from "react";
import useChannelList from "./useChannelList";

const useGetChannel = (channelID) => {

    const { channels, dm_channels } = useChannelList()

    const channelDetails = useMemo(() => {
        if (!channelID) {
            return null
        }

        const channel = channels.find(channel => channel.name === channelID)
        if (channel) {
            return channel
        }

        const dm_channel = dm_channels.find(dm_channel => dm_channel.name === channelID)
        if (dm_channel) {
            return dm_channel
        }

        return null
    }, [channels, dm_channels, channelID])

    return channelDetails
}

export default useGetChannel;