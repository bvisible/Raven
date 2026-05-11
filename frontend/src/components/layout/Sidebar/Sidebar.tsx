import { SidebarHeader } from "./SidebarHeader";
import { SidebarBody } from "./SidebarBody";
import { Box, Flex, Separator } from "@radix-ui/themes";
import { HStack } from "../Stack";
import WorkspacesSidebar from "./WorkspacesSidebar";
import { FrappeSidebar } from "@neoffice/frappe-sidebar-react";

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
            {!FRAPPE_INTEGRATION && <FrappeSidebar fixed={false} />}
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
