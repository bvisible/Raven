import { Skeleton } from "@components/ui/skeleton"

/** Suspense fallback with the setup page's frame: header, then the card. */
export const SetupPageSkeleton = () => (
    <div className="flex min-h-dvh flex-col bg-surface-gray-1">
        <div className="flex items-center justify-between gap-4 px-6 py-4">
            <Skeleton className="size-8 rounded-md" />
            <Skeleton className="hidden h-6 w-80 rounded-sm sm:block" />
            <span className="w-20" />
        </div>
        <div className="flex flex-1 justify-center pb-10 sm:items-center sm:px-4">
            <div className="flex min-h-[600px] w-full max-w-5xl flex-col gap-4 bg-surface-base p-8 sm:rounded-2xl sm:p-10 sm:shadow-sm">
                <Skeleton className="h-2 w-full rounded-sm" />
                <Skeleton className="mt-6 h-7 w-64 rounded-sm" />
                <Skeleton className="h-4 w-96 max-w-full rounded-sm" />
            </div>
        </div>
    </div>
)
