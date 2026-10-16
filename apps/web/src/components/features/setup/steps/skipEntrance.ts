import { createContext } from "react"

/** Skip slides in only when it appears; a step after one that had it shows it still. */
export const skipEnters = ({ previousHadSkip, hasSkip }: { previousHadSkip: boolean; hasSkip: boolean }) =>
    hasSkip && !previousHadSkip

/** Whether the last footer shown had Skip. Footers remount per step, so the page holds it. */
export const SkipMemoryContext = createContext<{ current: boolean } | null>(null)
