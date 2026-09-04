import { Link, router, Stack } from 'expo-router';
import { Button } from '@components/nativewindui/Button';
import CrossIcon from '@assets/icons/CrossIcon.svg';
import { useColorScheme } from '@hooks/useColorScheme';
import { View, Platform } from 'react-native';
import HashIcon from '@assets/icons/HashIcon.svg';
import PlusIcon from '@assets/icons/PlusIcon.svg';
import UserIcon from '@assets/icons/UserIcon.svg';
import useGetChannels from '@raven/lib/hooks/useGetChannels';
import useGetDirectMessageChannels from '@raven/lib/hooks/useGetDirectMessageChannels';
import { useGetUser } from '@raven/lib/hooks/useGetUser';
import { useState } from 'react';
import SearchInput from '@components/common/SearchInput/SearchInput';
import { useDebounce } from '@raven/lib/hooks/useDebounce';
import { ActionButtonLarge } from '@components/common/Buttons/ActionButtonLarge';
import { ChannelListItem, DMChannelListItem } from '@raven/types/common/ChannelListItem';
import ChannelRowItem from '@components/common/CommonListItems/ChannelRowItem';
import DMRowItem from '@components/common/CommonListItems/DMRowItem';
import { Text } from '@components/nativewindui/Text';
import { LegendList } from '@legendapp/list';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export default function QuickSearch() {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const openMenuItemSheet = (url: string) => {
        router.back()
        router.push(url, { relativeToDirectory: false })
    }

    const [searchQuery, setSearchQuery] = useState('')
    const combinedList = useCombinedChannelAndDMList(searchQuery)

    const onChannelPress = (channel: ChannelListItem | DMChannelListItem) => {
        router.back()
        router.push(`../../chat/${channel.name}`)
    }

    return <>
        <Stack.Screen options={{
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            title: t('search.quickSearch'),
            headerLeft: Platform.OS === 'ios' ? () => {
                return (
                    <Link asChild href="../" relativeToDirectory>
                        <Button variant="plain" className="ios:px-0" hitSlop={10}>
                            <CrossIcon color={colors.icon} height={24} width={24} />
                        </Button>
                    </Link>
                )
            } : undefined,
        }} />
        <View className="flex flex-col gap-3 p-3">
            <View>
                <SearchInput
                    onChangeText={setSearchQuery}
                    value={searchQuery}
                    autoFocus
                />
            </View>
            <View className='flex flex-row justify-center gap-2'>
                <ActionButtonLarge
                    onPress={() => openMenuItemSheet('../home/browse-channels')}
                    icon={<HashIcon fill={colors.grey} height={20} width={20} />}
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text={t('search.viewChannels')}
                    textProps={{ className: 'text-sm text-muted-foreground' }}
                />
                <ActionButtonLarge
                    onPress={() => openMenuItemSheet('../home/create-dm')}
                    icon={<UserIcon fill={colors.grey} height={20} width={20} />}
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text={t('directMessages.createDM')}
                    textProps={{ className: 'text-sm text-muted-foreground' }}
                />
                <ActionButtonLarge
                    onPress={() => openMenuItemSheet('../home/create-channel')}
                    icon={<PlusIcon fill={colors.grey} height={20} width={20} />}
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    text={t('search.newChannel')}
                    textProps={{ className: 'text-sm text-muted-foreground' }}
                />
            </View>
            <LegendList
                data={combinedList}
                keyExtractor={(item) => item.name}
                estimatedItemSize={42}
                renderItem={({ item }) =>
                    item.type === 'channel' ? (
                        <ChannelRowItem key={item.name} channel={item as ChannelListItem} onPress={onChannelPress} />
                    ) : (
                        <DMRowItem key={item.name} dmChannel={item as DMChannelListItem} onPress={onChannelPress} />
                    )
                }
                contentContainerStyle={{ paddingBottom: 180 }}
                showsVerticalScrollIndicator={false}
                ListEmptyComponent={
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    <Text className="px-2 py-2 text-sm text-muted-foreground">{t('search.noResultsFor', { query: searchQuery })}</Text>
                }
            />
        </View>
    </>
}

/**
 * Combines channels and DMs and filters them based on the search query
 * @param searchQuery - The search query to filter the channels and DMs by
 * @returns A list of channels and DMs that match the search query
 */
export const useCombinedChannelAndDMList = (searchQuery: string) => {

    const debouncedSearchQuery = useDebounce(searchQuery, 200)
    const { channels } = useGetChannels({ showArchived: false })
    const { dmChannels } = useGetDirectMessageChannels()

    // Filter channels
    const filteredChannels = channels
        .filter(channel => channel.channel_name.toLowerCase().includes(debouncedSearchQuery.toLowerCase()))
        .map(channel => ({ ...channel, type: 'channel' }))

    // Filter DMs
    const filteredDms = dmChannels
        .map(dm => ({
            ...dm,
            user: useGetUser(dm.peer_user_id),
            type: 'dm',
        }))
        .filter(dm => dm.user?.full_name?.toLowerCase().includes(debouncedSearchQuery.toLowerCase()))

    return [...filteredChannels, ...filteredDms]
}