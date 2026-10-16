import { ChannelPageSkeleton, DirectMessagePageSkeleton } from "@components/features/dm-channel/DirectMessagePageSkeleton"
import type { SetupStepName } from "../steps"
import type { PreviewModel } from "./model"
import { PreviewChannelSidebar } from "./PreviewChannelSidebar"
import { PreviewDMHeader } from "./PreviewDMHeader"
import { PreviewDMSidebar } from "./PreviewDMSidebar"
import { PreviewRail } from "./PreviewRail"

/** Raven as it's being set up: a window from the rail across, cut off at the form column. */
export const SetupPreview = ({ model, activeStep }: { model: PreviewModel; activeStep: SetupStepName }) => {
    // The team, and then their leave from Frappe HR, show in the DM sidebar, as the app would open it.
    const dmsOpen = activeStep === "team" || activeStep === "hr"
    // On the HR step a DM is open: with the first person in the list, or yourself.
    const peer = activeStep === "hr" ? model.people.find((person) => person.name) ?? model.profile : undefined
    return (
        <div className="flex h-full w-full flex-col py-10 ps-10">
            {/* Wider than the pane, so the chat island runs past its right edge and is cut off there. */}
            <div className="flex min-h-0 w-[calc(100%+16rem)] flex-1 overflow-hidden rounded-s-xl border border-e-0 border-outline-gray-2 bg-surface-sidebar shadow-xl animate-setup-open">
                <PreviewRail model={model} activeStep={activeStep} dmsOpen={dmsOpen} />
                <div key={dmsOpen ? "dms" : "channels"} className="flex h-full shrink-0 animate-setup-blur-in">
                    {dmsOpen ? <PreviewDMSidebar model={model} /> : <PreviewChannelSidebar model={model} activeStep={activeStep} />}
                </div>
                {/* The chat area as the app shows it while loading, for the view that's open. */}
                {dmsOpen ? (
                    <DirectMessagePageSkeleton title={peer && <PreviewDMHeader name={peer.name} image={peer.image} onLeave={model.leave} />} />
                ) : (
                    <ChannelPageSkeleton />
                )}
            </div>
        </div>
    )
}
