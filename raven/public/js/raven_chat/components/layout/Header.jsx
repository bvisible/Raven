import * as React from "react";
//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import useGetChannel from "../../hooks/useGetChannel";
import useGetUser from "../../hooks/useGetUser";
//// Neoffice - import order only, no behaviour change.
import Avatar from "../common/Avatar";
import ChannelIcon from "../common/ChannelIcon";

//// Neoffice - the brand's hand-drawn chat bubble, the icon the cockpit shows for this app (served by neoffice_theme:
//// Streamline's licence keeps the drawing out of this public repository). The desk's dark theme inverts it.
const BRAND_ICON = "/assets/neoffice_theme/icons/streamline/chat-bubble-text.svg"
/**
 * Header will have the following:
 * - Logo
 * - TODO: Unread message count
 * - Expand button
 */
/*
//// change name
*/
const Header = ({
    toggle, selectedChannel, isOpen, setSelectedChannel, unreadMessageCount
}) => {

    const closeChannel = () => {
        setSelectedChannel('')
    }

    const toggleRaven = () => {
        closeChannel()
        toggle()
    }

    return <div className="raven-header">
        {selectedChannel ? <ChannelHeader channelID={selectedChannel} onBackClick={closeChannel} /> :
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.2rem',
            }}>
            {/* //// Neoffice - the app's icon and name as the cockpit's menu shows them (« Messagerie d'entreprise »), in
                //// place of upstream's Raven wordmark (it read "synk" from 49ee6e172 to 2026-10-27). */}
                <span role='button' className="raven-logo" onClick={toggle}>
                    <img className="raven-logo-icon" src={BRAND_ICON} alt="" />
                    {__("Business messaging")}
                </span>

                <a href='/raven' target='_blank' className='btn btn-xs open-raven-button' style={{
                    lineHeight: '1.4rem',
                    // width: "24px",
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    // height: "24px",
                    // marginTop: '0.2rem',
                //// Neoffice - tooltip in the app's name (upstream: "Open Raven").
                }} title={__("Open the business messaging")}>
                    <svg
                        width="18"
                        height="18"
                        // fill='white'
                        viewBox="0 0 24 24"
                        // fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            d="M15.6396 7.02527H12.0181V5.02527H19.0181V12.0253H17.0181V8.47528L12.1042 13.3892L10.6899 11.975L15.6396 7.02527Z"
                        // fill="currentColor"
                        />
                        <path
                            d="M10.9819 6.97473H4.98193V18.9747H16.9819V12.9747H14.9819V16.9747H6.98193V8.97473H10.9819V6.97473Z"
                        // fill="currentColor"
                        />
                    </svg>
                </a>
            </div>

        }
        <div>
            {/* //// Neoffice - translated: the count read "N unread" in English on a French desk. */}
            {unreadMessageCount ? <span className="raven-unread-count">{__("{0} unread", [unreadMessageCount])}</span> : null}
            <button className="btn btn-md back-button" onClick={toggleRaven}>
                {isOpen ?
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="m16.192 6.344-4.243 4.242-4.242-4.242-1.414 1.414L10.535 12l-4.242 4.242 1.414 1.414 4.242-4.242 4.243 4.242 1.414-1.414L13.364 12l4.242-4.242z"></path></svg>
                    :
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="m6.293 13.293 1.414 1.414L12 10.414l4.293 4.293 1.414-1.414L12 7.586z"></path></svg>
                }
            </button>
        </div>

    </div>
}

export default Header


const ChannelHeader = ({ channelID, onBackClick }) => {

    const channel = useGetChannel(channelID)

    return <div className="raven-channel-header">
        <button className="btn btn-md back-button" onClick={onBackClick}>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M13.293 6.293 7.586 12l5.707 5.707 1.414-1.414L10.414 12l4.293-4.293z"></path></svg>
        </button>

        {/* //// Neoffice — the tooltip read "Open channel in Raven"; it names the app as the cockpit's menu does. */}
        {channel?.is_direct_message ? <DMChannelHeader channel={channel} /> :
            <a href={`/raven/channel/${channelID}`} target="_blank" title={__("Open the channel in the business messaging")}>
                <ChannelIcon channelType={channel?.channel_type} />
                <span className="raven-channel-header-name cal-sans">{channel?.channel_name ?? channelID}</span>
            </a>

        }
    </div>
}

const DMChannelHeader = ({ channel }) => {

    const user = useGetUser(channel.peer_user_id)
    //// Neoffice — the tooltip read "Open channel in Raven"; it names the app as the cockpit's menu does.
    return <a title={__("Open the channel in the business messaging")} className="raven-dm-channel-header" href={`/raven/channel/${channel.name}`} target="_blank">
        <Avatar user={user} fallback={channel.peer_user_id} />
        <span className="raven-channel-header-name cal-sans">{user?.full_name ?? user?.name}</span>
    </a>

}