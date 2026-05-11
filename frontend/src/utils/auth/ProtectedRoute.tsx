import { Stack } from '@/components/layout/Stack'
import { Flex, Text } from '@radix-ui/themes'
import { useContext } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { UserContext } from './UserProvider'
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
                <Text size='7' className='cal-sans tracking-normal'>neoffice</Text>
                <Text color='gray' weight='medium'>Setting up your workspace...</Text>
            </Stack>
        </Flex>
    }
    else if (!currentUser || currentUser === 'Guest') {
        return <Navigate to="/login" />
    }

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
}
