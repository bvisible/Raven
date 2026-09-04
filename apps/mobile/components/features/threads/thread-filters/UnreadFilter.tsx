import { View } from 'react-native';
import * as DropdownMenu from 'zeego/dropdown-menu';
import FilterIcon from '@assets/icons/FilterIcon.svg';
import { useColorScheme } from '@hooks/useColorScheme';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const UnreadFilter = ({ onlyShowUnread, setOnlyShowUnread }: { onlyShowUnread: boolean, setOnlyShowUnread: (onlyShowUnread: boolean) => void }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    return (
        <View>
            <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                    <View className={`items-center p-2 border border-border rounded-lg w-fit ${onlyShowUnread ? 'border-primary bg-primary/5' : ''}`}>
                        <FilterIcon color={colors.icon} height={18} width={18} />
                    </View>
                </DropdownMenu.Trigger>
                <DropdownMenu.Content side='bottom' align='end'>
                    <DropdownMenu.Item key="all" onSelect={() => setOnlyShowUnread(false)}>
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <DropdownMenu.ItemTitle>{t('common.all')}</DropdownMenu.ItemTitle>
                    </DropdownMenu.Item>
                    <DropdownMenu.Item key="unread" onSelect={() => setOnlyShowUnread(true)}>
                        {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                        <DropdownMenu.ItemTitle>{t('threads.unreadThreads')}</DropdownMenu.ItemTitle>
                    </DropdownMenu.Item>
                </DropdownMenu.Content>
            </DropdownMenu.Root>
        </View>
    )
}

export default UnreadFilter