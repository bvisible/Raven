import { Sheet, useSheetRef } from "@components/nativewindui/Sheet";
import { BottomSheetModal, BottomSheetView } from "@gorhom/bottom-sheet";
import { Pressable, View } from "react-native"
import { Button } from "@components/nativewindui/Button";
import { Text } from "@components/nativewindui/Text";
import { FrappeDoc, useFrappeUpdateDoc, useSWRConfig } from "frappe-react-sdk";
import { ChannelListItem } from "@raven/types/common/ChannelListItem";
import { toast } from "sonner-native";
import GlobeIcon from "@assets/icons/GlobeIcon.svg";
import LockIcon from "@assets/icons/LockIcon.svg";
import HashIcon from "@assets/icons/HashIcon.svg";
import { useColorScheme } from "@hooks/useColorScheme";
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';
import { TFunction } from 'i18next';

export const ChangeChannelType = ({ channelData }: { channelData: FrappeDoc<ChannelListItem> | undefined }) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const bottomSheetModalRef = useSheetRef()
    const { colors } = useColorScheme()
    const changeChannelTypeButtons = channelData ? getChangeChannelType({
        channelData,
        bottomSheetModalRef,
        iconMap: {
            'Public': <GlobeIcon height={18} width={18} fill={colors.icon} />,
            'Private': <LockIcon height={18} width={18} fill={colors.icon} />,
            'Open': <HashIcon height={18} width={18} fill={colors.icon} />
        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t threaded into getChangeChannelType, which is a plain
        //// factory function and cannot call useTranslation itself.
        },
        t
    }) : []

    return (
        <>
            {changeChannelTypeButtons.map((button) => (
                <Pressable key={button.id}
                    onPress={button.onPress}
                    className='flex flex-row items-center py-3 px-4 rounded-xl gap-2 bg-background dark:bg-card active:bg-card-background/50 dark:active:bg-card/80'>
                    {button.icon}
                    <Text className="text-base">{button.title}</Text>
                </Pressable>
            ))}

            <ChangeChannelTypeSheet channelData={channelData} bottomSheetModalRef={bottomSheetModalRef} />
        </>
    )
}


interface ChangeChannelTypeSheetProps {
    channelData: FrappeDoc<ChannelListItem> | undefined;
    bottomSheetModalRef: React.RefObject<BottomSheetModal>;
}

type ChannelType = 'Public' | 'Private' | 'Open';

const ChangeChannelTypeSheet = ({ channelData, bottomSheetModalRef }: ChangeChannelTypeSheetProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { mutate } = useSWRConfig()
    const { updateDoc, loading: updatingDoc, error } = useFrappeUpdateDoc();

    const getAlertSubMessage = (newChannelType: ChannelType) => {
        switch (newChannelType) {
            case 'Public':
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                return t('channels.convertToPublicInfo');
            case 'Private':
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                return t('channels.convertToPrivateInfo');
            case 'Open':
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                return t('channels.convertToOpenInfo');
            default:
                return '';
        }
    }

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): upstream renders the raw ChannelType value
    //// ('Public'/'Private'/'Open') lowercased. Map it to a translated label instead.
    const getChannelTypeName = (type: ChannelType) => {
        switch (type) {
            case 'Public':
                return t('channels.public');
            case 'Private':
                return t('channels.private');
            case 'Open':
                return t('channels.open');
            default:
                return type.toLowerCase();
        }
    }

    const changeChannelType = (newChannelType: 'Public' | 'Private' | 'Open') => {
        updateDoc("Raven Channel", channelData?.name ?? null, {
            type: newChannelType
        }).then(() => {
            mutate(["channel_members", channelData?.name])
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('channels.channelTypeChanged', { type: getChannelTypeName(newChannelType) }));
            handleClose();
        });
    };

    const handleClose = () => {
        bottomSheetModalRef.current?.dismiss();
    }

    return (
        <Sheet ref={bottomSheetModalRef}>
            {(props: { data: { newChannelType: ChannelType } } & any) => {
                return (
                    <BottomSheetView {...props}>
                        <View className="flex-col px-4 gap-3 mt-2 mb-20">
                            <Text className="text-xl font-cal-sans">
                                {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                                {t('channels.convertToTypeConfirm', { type: getChannelTypeName(props.data?.newChannelType) })}
                            </Text>
                            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                            <Text className="text-sm">{t('channels.convertToTypeWarning', { channelName: channelData?.channel_name, type: getChannelTypeName(props.data?.newChannelType) })}
                            </Text>
                            <Text className="text-sm">
                                {getAlertSubMessage(props.data?.newChannelType)}
                            </Text>
                            <View className="flex-col gap-3 pt-1">
                                <Button onPress={() => changeChannelType(props.data?.newChannelType)}
                                    disabled={updatingDoc}>
                                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                                    <Text>{updatingDoc ? t('channels.converting') : t('common.convert')}</Text>
                                </Button>
                                <Button onPress={handleClose} variant="plain" className="border border-border">
                                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                                    <Text>{t('common.cancel')}</Text>
                                </Button>
                            </View>
                        </View>
                    </BottomSheetView>
                )
            }}
        </Sheet>
    )
}


/**
 * channel type can be - Private, Public, Open
 * Change Channel Type would take in current channel type and change it to the next type depending on the current type
 * Example: If current channel type is Public, Change Channel Type would change it to Private or Open, so it returns two list item buttons accordingly
 * For current type Private - it would return Public and Open
 * For current type Open - it would return Public and Private
 * For current type Public - it would return Private and Open
*/
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t added to the factory's parameter object.
const getChangeChannelType = ({ channelData, bottomSheetModalRef, iconMap, t }: { channelData: ChannelListItem, bottomSheetModalRef: React.RefObject<BottomSheetModal>, iconMap: Record<string, React.ReactNode>, t: TFunction }) => {

    const channelType = channelData?.type as ChannelType

    const channelTypeMap = {
        'Public': ['Private', 'Open'],
        'Private': ['Public', 'Open'],
        'Open': ['Public', 'Private']
    }

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): same translated ChannelType label as above, for the
    //// action-sheet variant. TO REVIEW: the two copies of getChannelTypeName are identical.
    const getChannelTypeName = (type: ChannelType) => {
        switch (type) {
            case 'Public':
                return t('channels.public');
            case 'Private':
                return t('channels.private');
            case 'Open':
                return t('channels.open');
            default:
                return type.toLowerCase();
        }
    }

    const channelTypeList = channelTypeMap[channelType] as ChannelType[]

    const channelSettingsData = channelTypeList.map((type) => {
        return {
            id: type,
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            title: t('channels.convertToType', { type: getChannelTypeName(type) }),
            onPress: () => {
                bottomSheetModalRef.current?.present({
                    newChannelType: type,
                })
            },
            icon: iconMap[type]
        }
    })

    return channelSettingsData
}