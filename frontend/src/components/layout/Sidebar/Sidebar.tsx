import { SidebarHeader } from "./SidebarHeader";
import { SidebarBody } from "./SidebarBody";
import { Box, Flex, Separator } from "@radix-ui/themes";
import { HStack } from "../Stack";
import WorkspacesSidebar from "./WorkspacesSidebar";
//// Neoffice - NeoCockpit rail (549919c71, 2026-06-10 "feat(cockpit): consume shared NeoCockpit" + 1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven").
//// The SPA mounts the shared NeoCockpit chrome, but ONLY when it is served standalone: inside
//// /raven the FrappeLayout already renders it, and mounting both stacked two sidebars.
import { NeoCockpit } from "@neoffice/frappe-sidebar-react";

// Frappe Shell Native: when the SPA runs embedded inside Frappe (/raven), the
// FrappeLayout already provides the native sidebar (50px collapsed + hover
// expand + app switcher). We must NOT render the legacy package sidebar then,
// otherwise we get two stacked sidebars.
const FRAPPE_INTEGRATION =
    typeof window !== 'undefined' &&
    (window as unknown as { __FRAPPE_INTEGRATION__?: boolean }).__FRAPPE_INTEGRATION__ === true

export const Sidebar = () => {
    return (
        <HStack gap='0' className="h-screen">
            {/* //// Neoffice - NeoCockpit rail (549919c71, 2026-06-10 "feat(cockpit): consume shared NeoCockpit"): the workspace rail and channel list
                //// move into a bordered Flex so they read as one panel beside the cockpit rail
                //// (d8c324315, 2026-01-07 "fix: restore bg-gray-2 background on Raven sidebar parts"). */}
            {!FRAPPE_INTEGRATION && <NeoCockpit env="spa" layout="sidebar" />}
            <Flex className="bg-gray-2 dark:bg-gray-1 border-r border-r-gray-3">
                <WorkspacesSidebar />
                <Flex justify='between' direction='row' gap='2' width='100%'>
                    <Flex direction='column' gap='2' width='100%'>
                        <SidebarHeader />
                        <Box px='2'>
                            <Separator size='4' className={`bg-gray-4 dark:bg-gray-6`} />
                        </Box>
                        <SidebarBody />
                    </Flex>
                </Flex>
            </Flex>
        </HStack>

    )
}
