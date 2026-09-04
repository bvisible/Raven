//// Neoffice - import order only (an IDE "organize imports" pass ran on this file).
//// No import added or removed, no behaviour change.
import { UserContext } from '@/utils/auth/UserProvider';
import { Box, Flex, Heading } from '@radix-ui/themes';
//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import { PropsWithChildren, useContext } from 'react';
import { Link } from 'react-router-dom';
//// Neoffice - import order only (an IDE "organize imports" pass), no behaviour change.
import { FullPageLoader } from "./Loaders/FullPageLoader";


const AuthContainer = ({ children, ...props }: PropsWithChildren) => {
    const { isLoading } = useContext(UserContext)

    return (
        <Box className={'min-h-screen'}>
            <Flex justify='center' align='center' className={'min-h-screen w-full dark:bg-[#191919]'}>
                {
                    isLoading ? <FullPageLoader /> :
                        <Box className={'w-full max-w-md p-8'}>
                            <Flex direction='column' gap='6' className={'w-full'}>

                                <Link to="/" tabIndex={-1}>
                                    <Flex>
                                        {/* //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk" / 49ee6e172, 2025-04-05): login wordmark. */}
                                        <Heading size='9' className='cal-sans leading-normal tracking-normal w-fit'>synk</Heading>
                                    </Flex>
                                </Link>
                                {children}
                            </Flex>
                        </Box>
                }
            </Flex>
        </Box>
    )

}

export default AuthContainer;