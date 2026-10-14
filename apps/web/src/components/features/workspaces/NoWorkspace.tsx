import { useEffect, useRef, useState } from "react"
import { useFrappePostCall, useSWRConfig } from "frappe-react-sdk"
import { LayoutGrid } from "lucide-react"
import AppMobileFooter from "@components/features/header/AppMobileFooter"
import CreateWorkspaceButton from "@components/features/settings/panels/Workspaces/AddWorkspaceDialog"
import { Button } from "@components/ui/button"
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@components/ui/empty"
import ErrorBanner from "@components/ui/error-banner"
import { Spinner } from "@components/ui/spinner"
import { hasRole } from "@lib/permissions"
import _ from "@lib/translate"

/**
 * Home for a user in no workspace: joins them to the default one, after which
 * the refreshed workspace list sends "/" there. Empty state when there's none.
 */
const NoWorkspace = () => {
    const { mutate } = useSWRConfig()
    const { call, loading, error } = useFrappePostCall<{ message: string | null }>("raven.api.workspaces.join_default_workspace")
    const [noneToJoin, setNoneToJoin] = useState(false)

    const refreshWorkspaces = () => Promise.all([mutate("workspaces_list"), mutate("channel_list")])

    const join = () =>
        call({})
            .then((response) => {
                if (response.message) return refreshWorkspaces()
                setNoneToJoin(true)
            })
            .catch(() => { })

    // Once per mount: StrictMode's double effect would race two joins on the server.
    const started = useRef(false)
    useEffect(() => {
        if (started.current) return
        started.current = true
        join()
    })

    return (
        <div className="flex h-dvh flex-col">
            <div className="flex flex-1 items-center justify-center p-4">
                {error ? (
                    <div className="flex max-w-md flex-col gap-3">
                        <ErrorBanner error={error} />
                        <Button variant="outline" onClick={join} loading={loading}>{_("Retry")}</Button>
                    </div>
                ) : noneToJoin ? (
                    <Empty>
                        <EmptyMedia>
                            <LayoutGrid />
                        </EmptyMedia>
                        <EmptyHeader>
                            <EmptyTitle>{_("No workspaces to join yet")}</EmptyTitle>
                            <EmptyDescription>{_("Ask an admin to add you to a workspace.")}</EmptyDescription>
                        </EmptyHeader>
                        {hasRole("Raven Admin") && (
                            <EmptyContent>
                                <CreateWorkspaceButton label={_("Create a workspace")} onCreated={refreshWorkspaces} />
                            </EmptyContent>
                        )}
                    </Empty>
                ) : (
                    <Spinner />
                )}
            </div>
            <AppMobileFooter />
        </div>
    )
}

export default NoWorkspace
