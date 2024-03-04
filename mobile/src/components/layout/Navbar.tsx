import { IonIcon, IonLabel, IonRouterOutlet, IonTabBar, IonTabButton, IonTabs } from "@ionic/react"
import { BiChat, BiHash, BiUser } from "react-icons/bi"
import { Redirect, Route } from "react-router-dom"
import { Channels } from "../../pages/channels"
import { DirectMessageList } from "../../pages/direct-messages/DirectMessageList"
import { Profile } from "../../pages/profile"
import { PropsWithChildren, useContext } from "react"
import { UserContext } from "../../utils/auth/UserProvider"
import { FullPageLoader } from "./loaders/FullPageLoader"
import { Login } from "../../pages/auth"

export const Navbar = () => {
    const { currentUser, isLoading } = useContext(UserContext)
    return <IonTabs>
        <IonRouterOutlet>
            <Route exact path="/:tab(channels)">
                <ProtectedRoute>
                    <Channels />
                </ProtectedRoute>
            </Route>
            <Route exact path="/:tab(direct-messages)">
                <ProtectedRoute>
                    <DirectMessageList />
                </ProtectedRoute>
            </Route>
            {/* <Route exact path="/:tab(search)">
                <Search />
            </Route> */}
            {/* <Route exact path="/:tab(notifications)">
                <Notifications />
            </Route> */}
            <Route exact path="/:tab(profile)">
                <ProtectedRoute>
                    <Profile />
                </ProtectedRoute>
            </Route>
        </IonRouterOutlet>
        <IonTabBar slot="bottom" className="pb-6 pt-1 border-t-zinc-900 border-t-[1px]" hidden={isLoading || !currentUser || currentUser === "Guest"}>
            <IonTabButton tab="channels" href="/channels">
                <IonIcon hidden />
                <BiHash size={24} className="mb-0.5" />
                <IonLabel className="font-semibold">Canaux</IonLabel>
            </IonTabButton>
            <IonTabButton tab="direct-messages" href="/direct-messages">
                <IonIcon hidden />
                <BiChat size={24} className="mb-0.5" />
                <IonLabel className="font-semibold">MD</IonLabel>
            </IonTabButton>
            {/* <IonTabButton tab="search" href="/search">
                <BiSearch size={30} />
            </IonTabButton>
            <IonTabButton tab="notifications" href="/notifications">
                <BiBell size={30} />
            </IonTabButton> */}
            <IonTabButton tab="profile" href="/profile">
                <IonIcon hidden />
                <BiUser size={24} />
                <IonLabel className="font-semibold">Profil</IonLabel>
            </IonTabButton>
        </IonTabBar>
    </IonTabs>
}

export const ProtectedRoute = ({ children }: PropsWithChildren) => {
    const { currentUser, isLoading } = useContext(UserContext)

    if (isLoading) {
        return <FullPageLoader />
    }
    if (!currentUser || currentUser === 'Guest') {
        return <Login />
    } else {
        return children
    }
}