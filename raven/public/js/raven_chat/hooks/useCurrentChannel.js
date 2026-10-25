//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import { createContext, useContext } from "react";

const useCurrentChannel = () => {
    return useContext(CurrentChannelContext);
}

export default useCurrentChannel;

export const CurrentChannelContext = createContext('');