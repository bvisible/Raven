//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import useUserList from "./useUserList"

const useGetUser = (user_id = frappe.session.user) => {

    const { users = [] } = useUserList()

    const user = users?.message?.find(user => user.name === user_id)

    return user
}

export default useGetUser;