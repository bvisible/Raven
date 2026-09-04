import { useMemo, useState } from 'react';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): swapped react-native's Text for the NativeWind Text
//// used everywhere else in this app, so the translated strings inherit the same typography.
import { View } from 'react-native';
import { Text } from '@components/nativewindui/Text';
import { KeyboardAwareScrollView } from 'react-native-keyboard-controller';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { FlashList } from '@shopify/flash-list';
import { Member, useFetchChannelMembers } from '@raven/lib/hooks/useFetchChannelMembers';
import { useDebounce } from '@raven/lib/hooks/useDebounce';
import { UserFields } from '@raven/types/common/UserFields';
import { useUserListProvider } from '@raven/lib/providers/UserListProvider';
import { Divider } from '@components/layout/Divider';
import { useColorScheme } from '@hooks/useColorScheme';
import ChevronLeftIcon from '@assets/icons/ChevronLeftIcon.svg';
import ChannelMemberRow from '@components/features/channel-settings/Members/ChannelMemberRow';
import SearchInput from '@components/common/SearchInput/SearchInput';
import CommonErrorBoundary from '@components/common/CommonErrorBoundary';
import { TouchableOpacity } from 'react-native-gesture-handler';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const ChannelMembers = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()
    const insets = useSafeAreaInsets()

    const { id: channelId } = useLocalSearchParams()

    const [searchQuery, setSearchQuery] = useState('')
    const debouncedText = useDebounce(searchQuery, 200)

    const { channelMembers } = useFetchChannelMembers(channelId as string ?? "");
    const { enabledUsers } = useUserListProvider()
    const extractChannelMembers = Array.from(enabledUsers.values()).filter(user => channelMembers?.[user.name]);

    const filteredMembers = useMemo(() => {
        const lowerCaseInput = debouncedText?.toLowerCase() || ''
        return extractChannelMembers.filter((user: UserFields) => {
            if (!debouncedText) return true;

            return (
                user?.full_name.toLowerCase().includes(lowerCaseInput) ||
                user?.name.toLowerCase().includes(lowerCaseInput)
            )
        })
    }, [debouncedText, extractChannelMembers])

    return (
        <View className='flex-1 bg-background'>
            <Stack.Screen options={{
                headerStyle: { backgroundColor: colors.background },
                headerLeft: () => (
                    <TouchableOpacity onPress={() => router.back()} hitSlop={10}>
                        <ChevronLeftIcon stroke={colors.foreground} />
                    </TouchableOpacity>
                ),
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                headerTitle: () => <Text className='ml-2 text-base text-foreground font-semibold'>{t('common.members')}</Text>,
                headerRight: () => (
                    <TouchableOpacity onPress={() => router.push(`./add-members`)} hitSlop={10}>
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <Text className='text-base font-semibold text-primary dark:text-secondary'>{t('common.add')}</Text>
                    </TouchableOpacity>
                )
            }} />
            <View className='px-4 py-3'>
                <SearchInput
                    onChangeText={setSearchQuery}
                    value={searchQuery}
                />
            </View>
            <KeyboardAwareScrollView
                bottomOffset={8}
                keyboardShouldPersistTaps="handled"
                keyboardDismissMode="interactive"
                contentInsetAdjustmentBehavior="automatic"
                contentContainerStyle={{ paddingBottom: insets.bottom, height: "auto" }}
                bounces={false}
                showsVerticalScrollIndicator={false}>
                <View className='flex-1'>
                    <FlashList
                        data={filteredMembers}
                        renderItem={({ item }) => <ChannelMemberRow member={item as Member} />}
                        keyExtractor={(item) => item.name}
                        estimatedItemSize={64}
                        ItemSeparatorComponent={() => <Divider className='mx-0' />}
                        bounces={false}
                        showsVerticalScrollIndicator={false}
                        ListEmptyComponent={!debouncedText.length ? () => {
                            return (
                                <View className="flex-1 items-center justify-center">
                                    <Text className="text-[15px] text-center text-muted-foreground">
                                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                                        {t('members.noMembers')}
                                    </Text>
                                </View>
                            )
                        } : undefined}
                    />
                </View>
            </KeyboardAwareScrollView>

            {!filteredMembers.length && debouncedText.length ? (
                <View className="absolute inset-0 items-center justify-center h-60">
                    <Text className="text-[15px] text-center text-muted-foreground">
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        {t('search.noResultsFor', { query: debouncedText })}
                    </Text>
                </View>
            ) : null}

        </View>
    )
}

export default ChannelMembers

export const ErrorBoundary = CommonErrorBoundary