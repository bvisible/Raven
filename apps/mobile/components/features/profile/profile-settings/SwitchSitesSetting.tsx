import { Pressable, View } from 'react-native'
import { Text } from '@components/nativewindui/Text'
import { useColorScheme } from '@hooks/useColorScheme'
import { useCallback, useMemo } from 'react'
import useSiteContext from '@hooks/useSiteContext'
import { Sheet, useSheetRef } from '@components/nativewindui/Sheet'
import { getSiteNameFromUrl } from '@raven/lib/utils/operations'
import { BottomSheetScrollView } from '@gorhom/bottom-sheet'
import { BottomSheetView } from '@gorhom/bottom-sheet'
import AddSite from '@components/features/auth/AddSite'
import SiteSwitcher from '@components/features/auth/SiteSwitcher'
import ServerIcon from '@assets/icons/ServerIcon.svg'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

const SwitchSitesSetting = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const bottomSheetRef = useSheetRef()

    const siteInfo = useSiteContext()

    const urlWithoutProtocol = useMemo(() => {
        return getSiteNameFromUrl(siteInfo?.url)
    }, [siteInfo])

    const switchSite = useCallback(() => {
        bottomSheetRef.current?.present()
    }, [])

    const addSiteSheetRef = useSheetRef()

    const openAddSiteSheet = useCallback(() => {
        bottomSheetRef.current?.dismiss()
        addSiteSheetRef.current?.present()
    }, [])

    return (
        <>
            <Pressable onPress={switchSite} className='bg-background dark:bg-card rounded-xl active:bg-card-background/50 dark:active:bg-card/80'>
                <View className='flex flex-row py-0 pl-4 pr-2 items-center justify-between'>
                    <View className='flex-row items-center gap-2 py-2.5'>
                        <ServerIcon height={18} width={18} color={colors.icon} />
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className='text-base'>{t('sites.currentSite')}</Text>

                    </View>
                    <View className='flex-row h-10 items-center'>
                        <Text className='text-base overflow-hidden text-ellipsis text-muted-foreground/80'>{urlWithoutProtocol}</Text>
                    </View>
                </View>
            </Pressable>

            <Sheet enableDynamicSizing ref={bottomSheetRef}>
                <BottomSheetScrollView>
                    <View className='flex pb-24 flex-col gap-4 px-4'>
                        <SiteSwitcher openAddSiteSheet={openAddSiteSheet} />
                    </View>
                </BottomSheetScrollView>
            </Sheet>

            <Sheet enableDynamicSizing ref={addSiteSheetRef}>
                <BottomSheetView className='flex-1 pb-16'>
                    <View className='flex-1 gap-2 px-4'>
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className='text-lg font-semibold'>{t('sites.addNewSite')}</Text>
                        <AddSite useBottomSheet={true} />
                    </View>
                </BottomSheetView>
            </Sheet>
        </>
    )
}

export default SwitchSitesSetting