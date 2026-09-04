import { View } from 'react-native';
import { Stack } from 'expo-router';
import { useColorScheme } from '@hooks/useColorScheme';
import { useState } from 'react';
import { useDebounce } from '@raven/lib/hooks/useDebounce';
import SearchInput from '@components/common/SearchInput/SearchInput';
import MediaTabs from './MediaTabs';
import HeaderBackButton from '@components/common/Buttons/HeaderBackButton';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export type MediaInChannel = {
    name: string;
    channel_id: string;
    owner: string;
    full_name: string;
    user_image: string;
    creation: string;
    file_name: string;
    file_size: number;
    file_type: string;
    file_url: string;
    message_type: "File" | "Image";
    thumbnail_width?: number;
    thumbnail_height?: number;
    file_thumbnail?: string;
};

export default function Media() {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const [searchText, setSearchText] = useState("")
    const debouncedText = useDebounce(searchText, 400)

    return (
        <>
            <Stack.Screen options={{
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                title: t('media.imagesAndFiles'),
                headerLargeTitle: false,
                headerStyle: { backgroundColor: colors.background },
                headerLeft: () => <HeaderBackButton />,
            }} />
            <View className='flex-1 gap-3'>
                <View className='pt-3 px-3'>
                    <SearchInput
                        value={searchText}
                        onChangeText={setSearchText}
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                        placeholder={t('media.searchImagesAndFiles')}
                    />
                </View>
                <MediaTabs searchQuery={debouncedText} />
            </View>
        </>
    )
}