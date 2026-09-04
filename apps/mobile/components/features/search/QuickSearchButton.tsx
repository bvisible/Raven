import { Text } from '@components/nativewindui/Text'
import { useColorScheme } from '@hooks/useColorScheme'
import { TouchableOpacity, View } from 'react-native'
import SearchIcon from '@assets/icons/SearchIcon.svg';
import { router } from 'expo-router';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const QuickSearchButton = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { isDarkColorScheme } = useColorScheme()
    const searchIconColor = isDarkColorScheme ? '#9ca3af' : '#d1d5db'

    return (
        <View>
            <TouchableOpacity onPress={() => router.push('../home/quick-search', { relativeToDirectory: true })}>
                <View className={'flex-row items-center gap-2 rounded-lg px-3 py-1.5 bg-[#6c69cd] dark:bg-[#4c49ad]'}>
                    <SearchIcon width={16} height={16} fill={searchIconColor} />
                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                    <Text className='text-base text-gray-300 dark:text-gray-400'>{t('search.jumpToOrSearch')}</Text>
                </View>
            </TouchableOpacity>
        </View>
    )
}

export default QuickSearchButton