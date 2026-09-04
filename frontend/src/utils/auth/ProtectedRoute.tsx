//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import { Stack } from '@/components/layout/Stack'
import { Flex, Text } from '@radix-ui/themes'
import { useContext } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { UserContext } from './UserProvider'
//// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): the flag is set by raven.html
//// before the bundle loads. Read once at module scope - it never changes within a page.
import { FrappeLayout } from '@/components/layout/frappe'

// Frappe integration flag — set by raven/www/raven.html before the bundle
// loads. When true, authenticated routes are wrapped in the FrappeLayout
// (native sidebar + navbar) reimplemented locally and fed by the curated
// mini-boot. When false (vite standalone dev), routes render in their
// original chrome.
const FRAPPE_INTEGRATION =
    typeof window !== 'undefined' &&
    (window as unknown as { __FRAPPE_INTEGRATION__?: boolean }).__FRAPPE_INTEGRATION__ === true

export const ProtectedRoute = () => {

    const { currentUser, isLoading } = useContext(UserContext)

    if (isLoading) {
        return <Flex justify='center' align='center' height='100vh' width='100vw' className='animate-fadein'>
            <Stack className='text-center' gap='1'>
                {/* //// Neoffice - the loading wordmark says "neoffice", not the app name: this screen shows while
                    //// the session is still unknown, so it belongs to the suite, not to the chat app. */}
                <Text size='7' className='cal-sans tracking-normal'>neoffice</Text>
                <Text color='gray' weight='medium'>Setting up your workspace...</Text>
            </Stack>
        </Flex>
    }
    else if (!currentUser || currentUser === 'Guest') {
        return <Navigate to="/login" />
    }
    //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): authenticated routes render
    //// inside the Frappe chrome; /login, /signup and /forgot-password stay full-screen.

    if (FRAPPE_INTEGRATION) {
        return (
            <FrappeLayout>
                <Outlet />
            </FrappeLayout>
        )
    }

    return (
        <Outlet />
    )
//// Neoffice - newline at end of file. No code change.
}
