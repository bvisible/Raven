import { TouchableOpacity, View } from 'react-native'
import { useState } from 'react'
import { useDebounce } from '@raven/lib/hooks/useDebounce'
import { useColorScheme } from '@hooks/useColorScheme'
import ThreadsList from './ThreadsList'
import ChannelFilter from './thread-filters/ChannelFilter'
import { Text } from '@components/nativewindui/Text'
import { ChannelIcon } from '../channels/ChannelList/ChannelIcon'
import CrossIcon from '@assets/icons/CrossIcon.svg'
import { COLORS } from '@theme/colors'
import { Divider } from '@components/layout/Divider'
import UnreadFilter from './thread-filters/UnreadFilter'
import SearchInput from '@components/common/SearchInput/SearchInput'
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next'

/**
 * Component for displaying participating threads - where the user is a member of the thread
 */
const ParticipatingThreads = () => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const [onlyShowUnread, setOnlyShowUnread] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const debouncedText = useDebounce(searchQuery, 200)
    const { colors } = useColorScheme()
    const [channel, setChannel] = useState('all')

    return (
        <View className="flex flex-col">
            <View className='flex flex-col gap-3 px-3'>
                <View className="flex flex-row items-center gap-2">
                    <View className="flex-1 max-w-[80%]">
                        <SearchInput
                            onChangeText={setSearchQuery}
                            value={searchQuery}
                            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                            placeholder={t('common.search') + '...'}
                        />
                    </View>
                    <ChannelFilter channel={channel} setChannel={setChannel} />
                    <UnreadFilter onlyShowUnread={onlyShowUnread} setOnlyShowUnread={setOnlyShowUnread} />
                </View>
                {channel !== 'all' && (
                    <TouchableOpacity onPress={() => setChannel('all')} className="self-start">
                        <View className='flex flex-row items-center gap-1 px-2 py-1.5 bg-primary/10 dark:bg-primary/30 rounded-full'>
                            <ChannelIcon fill={colors.foreground} size={14} type={'channel'} />
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <Text className='text-xs font-medium'>{channel === 'all' ? t('common.all') : channel}</Text>
                            <View className='bg-slate-400 dark:bg-slate-600 rounded-full p-0.5 ml-1'>
                                <CrossIcon color={COLORS.white} height={10} width={10} />
                            </View>
                        </View>
                    </TouchableOpacity>
                )}
            </View>
            <Divider className='mx-0 mt-3' prominent />
            <ThreadsList
                content={debouncedText}
                channel={channel}
                onlyShowUnread={onlyShowUnread}
            />
        </View>
    )
}

export default ParticipatingThreads