import * as React from "react";
import useBoolean from "./hooks/useBoolean";
import Header from "./components/layout/Header";
import ChannelList from "./components/layout/ChannelList";
import { StartFetchContext } from "./hooks/useStartFetch";
import { SWRConfig } from "swr";
import ChatView from "./components/layout/Chat/ChatView";
import useUnreadCount from "./hooks/useUnreadCount";
import { CurrentChannelContext } from "./hooks/useCurrentChannel";

//// Neoffice - docked mode (4b543c6b9 + e58d43ae8, 2026-06-11 "feat(cockpit): docked chat widget"): under the NeoCockpit chrome the widget is
//// anchored next to the rail icon instead of floating at the bottom of the page.
export function App({ docked = false }) {

  //// Neoffice - docked mode (4b543c6b9 + e58d43ae8, 2026-06-11 "feat(cockpit): docked chat widget"): `off` is needed because a docked widget must
  //// close completely (there is no collapsed bar to fall back to).
  const [isOpen, { on, toggle, off }] = useBoolean(false)

  const [initOpen, setInitOpen] = React.useState(false)

  React.useEffect(() => {
    if (isOpen) {
      setInitOpen(true)
    }
  }, [isOpen])

  const [selectedChannel, setSelectedChannel] = React.useState('')

  const { totalUnread } = useUnreadCount()

  // //// NEOFFICE — docked mode (NeoCockpit): the widget has no visible
  // collapsed bar; the cockpit rail toggles it through window events and
  // reads the unread total back to paint its badge.
  React.useEffect(() => {
    if (!docked) return
    const handleToggle = () => toggle()
    const handleClose = () => off()
    window.addEventListener('raven-chat:toggle', handleToggle)
    window.addEventListener('raven-chat:close', handleClose)
    return () => {
      window.removeEventListener('raven-chat:toggle', handleToggle)
      window.removeEventListener('raven-chat:close', handleClose)
    }
  }, [docked, toggle, off])

  React.useEffect(() => {
    window.dispatchEvent(new CustomEvent('raven-chat:unread-count', { detail: totalUnread || 0 }))
  }, [totalUnread])

  return (
    <StartFetchContext.Provider value={initOpen}>
      <CurrentChannelContext.Provider value={selectedChannel}>
        <SWRConfig value={{
          revalidateOnFocus: false,
          revalidateOnMount: true,
          revalidateOnReconnect: false,
          revalidateIfStale: false,
        }}>
          <div className="raven-container" data-open-state={isOpen}>
            <Header
              on={on}
              toggle={toggle}
              isOpen={isOpen}
              selectedChannel={selectedChannel}
              setSelectedChannel={setSelectedChannel}
              unreadMessageCount={totalUnread} />
            <div className='raven-content-container' data-channel={selectedChannel} data-channel-list-view={selectedChannel ? 'false' : 'true'}>
              <ChannelList isOpen={isOpen} onSelectChannel={setSelectedChannel} />
              <ChatView selectedChannel={selectedChannel} />
            </div>
          </div>
        </SWRConfig>
      </CurrentChannelContext.Provider>
    </StartFetchContext.Provider>
  );
}