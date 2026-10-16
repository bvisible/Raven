import _ from "@lib/translate"
import { cn } from "@lib/utils"
import type { FinalePhase } from "./finale"

/** Raven's sign-off, a line at a time, on the steps' left edge; the expansion fades the last one. */
export const FinaleMessage = ({ phase }: { phase: FinalePhase }) => {
    const now = phase === "now" || phase === "now-out"
    return (
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center pb-[12vh]">
            {/* Keyed, so each line plays its own entrance. */}
            <h1
                key={now ? "now" : "send"}
                id="setup-title"
                className={cn("text-6xl font-bold text-ink-gray-9 md:text-8xl", phase === "now-out" ? "animate-setup-step-out" : "animate-setup-blur-in")}
            >
                {now ? _("Now,") : _("Send a Raven")}
            </h1>
        </div>
    )
}
