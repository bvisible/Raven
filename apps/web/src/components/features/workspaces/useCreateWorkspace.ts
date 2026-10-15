import { useFrappeCreateDoc, useFrappeFileUpload, useFrappeUpdateDoc, useSWRConfig } from "frappe-react-sdk"
import type { RavenWorkspace } from "@raven/types/Raven/RavenWorkspace"

/** Extends the generated type with the field that exists in the DocType but is not yet in the TS definition. */
export type WorkspaceFormData = RavenWorkspace & {
    only_admins_can_create_channels?: 0 | 1
}

/**
 * Creates a workspace, then attaches its logo: the upload needs the saved
 * record to attach to. Refreshes the workspace and channel lists once the
 * workspace exists, even if the logo upload then fails.
 */
export const useCreateWorkspace = () => {
    const { mutate } = useSWRConfig()
    const { createDoc, loading: creating, error } = useFrappeCreateDoc<WorkspaceFormData>()
    const { updateDoc, loading: updating } = useFrappeUpdateDoc()
    const { upload, loading: uploading, error: uploadError } = useFrappeFileUpload()

    // Awaitable: callers that open the new workspace need it in the list first.
    const refreshLists = () => Promise.all([mutate("workspaces_list"), mutate("channel_list")]).catch(() => { })

    const createWorkspace = (data: Partial<WorkspaceFormData>, logo?: File) =>
        // The rest of the fields take their DocType defaults.
        createDoc("Raven Workspace", data as WorkspaceFormData).then((workspace) => {
            if (!logo) return refreshLists().then(() => workspace)
            return upload(logo, {
                doctype: "Raven Workspace",
                docname: workspace.name,
                fieldname: "logo",
                otherData: { optimize: "1" },
                isPrivate: false,
            })
                .then((file) => updateDoc("Raven Workspace", workspace.name, { logo: file.file_url }))
                .then(() => workspace)
                .finally(refreshLists)
        })

    return { createWorkspace, loading: creating || uploading || updating, error, uploadError }
}
