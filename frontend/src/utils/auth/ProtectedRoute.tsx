import { useContext } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { FullPageLoader } from '@/components/layout/Loaders/FullPageLoader'
import { UserContext } from './UserProvider'
import { useEffect } from 'react';

export const ProtectedRoute = () => {

    const { currentUser, isLoading } = useContext(UserContext)
    /* ////
    if (isLoading) {
        return <FullPageLoader />
    }
    else if (!currentUser || currentUser === 'Guest') {
        return <Navigate to="/../login" />
    }
    */
    useEffect(() => {
        if (!isLoading && (!currentUser || currentUser === 'Guest')) {
            window.location.href = '/login';
        }
    }, [isLoading, currentUser]);

    if (isLoading) {
        return <FullPageLoader />;
    }

    if (!currentUser || currentUser === 'Guest') {
        return null;
    }
    ////
    return (
        <Outlet />
    )
}