//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import useSWR from "swr"
import { fetcher } from "./useFetch"
import useStartFetch from "./useStartFetch"

const useUserList = () => {

    /** Only fetch users when Raven is first opened */
    const startFetch = useStartFetch()

    const { data, error, isLoading } = useSWR(startFetch ? 'raven.api.raven_users.get_list' : null, fetcher, {
        revalidateOnFocus: false,
        revalidateOnMount: true,
        revalidateOnReconnect: false,
        revalidateIfStale: false,
    })

    return {
        users: data,
        isLoading,
        error
    }
}

export default useUserList;