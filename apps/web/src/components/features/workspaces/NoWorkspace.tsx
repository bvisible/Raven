import { LayoutGrid } from "lucide-react"
import AppMobileFooter from "@components/features/header/AppMobileFooter"
import CreateWorkspaceButton from "@components/features/settings/panels/Workspaces/AddWorkspaceDialog"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@components/ui/empty"
import { hasRole } from "@lib/permissions"
import _ from "@lib/translate"
import { isSetupPending } from "@utils/setup"

/**
 * Home for a user in no workspace. Admins add people to workspaces (setup's
 * invites do it directly); a new workspace refreshes the list, which sends "/" there.
 */
const NoWorkspace = () => (
    <div className="flex h-dvh flex-col">
        <div className="flex flex-1 items-center justify-center p-4">
            {/* Setup's card covers this; its own "Create" would compete with the card's. */}
            {!isSetupPending() && (
                <Empty>
                    <EmptyMedia>
                        <LayoutGrid />
                    </EmptyMedia>
                    <EmptyHeader>
                        <EmptyTitle>{_("You're not in a workspace yet")}</EmptyTitle>
                        <EmptyDescription>{_("Ask an admin to add you to a workspace.")}</EmptyDescription>
                    </EmptyHeader>
                    {hasRole("Raven Admin") && (
                        <EmptyContent>
                            <CreateWorkspaceButton label={_("Create a workspace")} />
                        </EmptyContent>
                    )}
                </Empty>
            )}
        </div>
        <AppMobileFooter />
    </div>
)

export default NoWorkspace
