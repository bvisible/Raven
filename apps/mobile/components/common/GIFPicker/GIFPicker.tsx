import { Image } from "expo-image";
import { useState } from "react";
import { View } from "react-native";
import { useDebounce } from "@raven/lib/hooks/useDebounce";
import GIFSearchResults from "./GIFSearchResults";
import GIFFeaturedResults from "./GIFFeaturedResults";
import SearchInput from "../SearchInput/SearchInput";
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export interface GIFPickerProps {
    onSelect: (gif: any) => void;
}

const GIFPicker = ({ onSelect }: GIFPickerProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const [searchText, setSearchText] = useState('');
    const debouncedText = useDebounce(searchText, 200);

    return (
        <View className="px-2 h-full relative">
            <View className="mb-3">
                <SearchInput
                    value={searchText}
                    onChangeText={setSearchText}
                    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                    placeholder={t('media.searchGIF')}
                />
            </View>

            {debouncedText.length >= 2 ? (
                <GIFSearchResults query={debouncedText} onSelect={onSelect} />
            ) : (
                <GIFFeaturedResults onSelect={onSelect} />
            )}

            <View className="flex-row items-center justify-center py-2 h-[50px] absolute bottom-0 left-0 right-0 bg-background">
                <Image
                    source={{
                        uri: "https://www.gstatic.com/tenor/web/attribution/PB_tenor_logo_blue_horizontal.png"
                    }}
                    contentFit="contain"
                    style={{ width: 100, height: 16 }}
                />
            </View>
        </View>
    );
};

export default GIFPicker;