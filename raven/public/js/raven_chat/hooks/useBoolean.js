//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import { useState, useCallback } from "react";

const useBoolean = (initialValue = false) => {
    const [value, setValue] = useState(initialValue);

    const toggle = useCallback(() => setValue((v) => !v), []);

    const on = useCallback(() => setValue(true), []);
    const off = useCallback(() => setValue(false), []);

    return [value, { toggle, on, off }];
}

export default useBoolean;