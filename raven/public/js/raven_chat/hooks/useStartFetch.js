//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import * as React from "react";

const useStartFetch = () => {
    return React.useContext(StartFetchContext)
}

export default useStartFetch;

/** Context to store whether the Raven chat module has been opened or not.
 * This is so that we can fetch data only when the module is opened.
 */
export const StartFetchContext = React.createContext(false)