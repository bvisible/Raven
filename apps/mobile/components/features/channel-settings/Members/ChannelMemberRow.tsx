import { View, Text, Alert, Pressable } from 'react-native';
import { useFrappeDeleteDoc, useFrappeGetCall, useFrappeUpdateDoc, useSWRConfig } from 'frappe-react-sdk';
import { useLocalSearchParams } from 'expo-router';
import Reanimated, { SharedValue, useAnimatedStyle } from 'react-native-reanimated';
import { Member, useFetchChannelMembers } from '@raven/lib/hooks/useFetchChannelMembers';
import UserAvatar from '@components/layout/UserAvatar';
import { Button } from '@components/nativewindui/Button';
import ReanimatedSwipeable from 'react-native-gesture-handler/ReanimatedSwipeable';
import TrashIcon from "@assets/icons/TrashIcon.svg"
import CrownIcon from "@assets/icons/CrownIcon.svg"
import useCurrentRavenUser from '@raven/lib/hooks/useCurrentRavenUser';
import { useActionSheet } from '@expo/react-native-action-sheet';
import { useCurrentChannelData } from '@hooks/useCurrentChannelData';
import { toast } from 'sonner-native';
import { ActivityIndicator } from '@components/nativewindui/ActivityIndicator';
import { COLORS } from '@theme/colors';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

const ChannelMemberRow = ({ member }: { member: Member }) => {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { id: channelId } = useLocalSearchParams()
    const { myProfile: currentUserInfo } = useCurrentRavenUser()
    const { channelMembers, mutate: updateMembers } = useFetchChannelMembers(channelId as string ?? "")
    const { updateDoc, loading: updatingMember, reset } = useFrappeUpdateDoc()
    const { channel } = useCurrentChannelData(channelId as string ?? "")
    const isAllowed = channelMembers[currentUserInfo?.name ?? ""]?.is_admin === 1 && member.name !== currentUserInfo?.name && channel?.channelData.type !== "Open" && channel?.channelData.is_archived === 0
    const isBot = member.type === "Bot"

    const { data: memberInfo } = useFrappeGetCall<{ message: { name: string } }>("frappe.client.get_value", {
        doctype: "Raven Channel Member",
        filters: JSON.stringify({ channel_id: channelId, user_id: member?.name }),
        fieldname: JSON.stringify(["name"]),
    }, undefined, {
        revalidateOnFocus: false
    })

    const updateAdminStatus = async (admin: 1 | 0) => {
        if (isBot) {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('members.botsCannotBeAdmins'))
            return
        }
        return updateDoc("Raven Channel Member", memberInfo?.message.name ?? "", {
            is_admin: admin,
        }).then(() => {
            updateMembers()
            reset()
            if (admin === 1) {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('members.madeAdmin', { name: member.full_name }))
            } else {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.warning(t('members.removedAdmin', { name: member.full_name }))
            }
        }).catch((e) => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('members.updateMemberFailed'))
            reset()
        })
    }

    function RightAction(prog: SharedValue<number>, drag: SharedValue<number>, member: Member) {

        const styleAnimation = useAnimatedStyle(() => {
            return {
                transform: [{ translateX: drag.value + 70 }],
            }
        })

        const { deleteDoc, error, loading: deletingDoc } = useFrappeDeleteDoc()
        const { mutate } = useSWRConfig()

        const { data: memberInfo, error: errorFetchingChannelMember } = useFrappeGetCall<{ message: { name: string } }>('frappe.client.get_value', {
            doctype: "Raven Channel Member",
            filters: JSON.stringify({ channel_id: channelId, user_id: member?.name }),
            fieldname: JSON.stringify(["name"])
        }, undefined, {
            revalidateOnFocus: false
        })

        const deleteMember = async () => {
            return deleteDoc('Raven Channel Member', memberInfo?.message.name).then(() => {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('members.removedFromChannel', { name: member.full_name }))
                mutate(["channel_members", channelId])
            })
        }

        const showAlert = () =>
            Alert.alert(
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                t('members.removeMemberConfirm'),
                t('members.removeMemberMessage', { name: member.full_name, channelName: channel?.channelData.channel_name }),
                [
                    {
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                        text: t('common.cancel'),
                    },
                    {
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                        text: t('common.remove'),
                        style: 'destructive',
                        onPress: deleteMember
                    },
                ]
            )

        return (
            <Reanimated.View style={styleAnimation}>
                <Button variant="plain" size="none" disabled={!isAllowed || deletingDoc} onPress={showAlert} style={{ width: 70, height: "100%" }} className={`bg-red-500 dark:bg-red-600 rounded-none items-center justify-center ${!isAllowed ? 'opacity-45' : ''}`}>
                    {deletingDoc ? <ActivityIndicator size="small" color={COLORS.white} /> : <TrashIcon width={22} height={22} fill="white" />}
                </Button>
            </Reanimated.View>
        )
    }

    const { showActionSheetWithOptions } = useActionSheet()

    const showActions = () => {

        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
        let options = [t('members.makeAdmin'), t('members.removeAdmin'), t('common.cancel')]
        const isAdmin = channelMembers[member.name].is_admin

        if (isAllowed) {
            showActionSheetWithOptions({
                options,
                cancelButtonIndex: 2,
                disabledButtonIndices: isAdmin ? [0] : [1],
                destructiveButtonIndex: isAdmin ? 1 : undefined,
            }, async (selectedIndex: number | undefined) => {
                switch (selectedIndex) {
                    case 0:
                        await updateAdminStatus(1)
                        break
                    case 1:
                        await updateAdminStatus(0)
                        break
                }
            })
        }
    }

    return (
        <ReanimatedSwipeable
            friction={2}
            enableTrackpadTwoFingerGesture
            rightThreshold={40}
            renderRightActions={(prog, drag) => RightAction(prog, drag, member)}>
            <View>
                <Pressable onLongPress={showActions} className='ios:active:bg-linkColor flex-row items-center justify-between rounded-lg'>
                    <View className='gap-3 px-4 py-3 flex-row items-center'>
                        <UserAvatar
                            src={member.user_image ?? ""}
                            alt={member.full_name ?? ""}
                            availabilityStatus={member.availability_status}
                        />
                        <View className='flex-col gap-0.5 justify-center'>
                            <View className='flex-row gap-2'>
                                <Text className='text-[15px] text-foreground font-medium'>
                                    {member.full_name?.length > 40
                                        ? `${member.full_name.slice(0, 40)}...`
                                        : member.full_name}
                                    {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
                                    {member.name === currentUserInfo?.name ? ` (${t('common.you')})` : ""}
                                </Text>
                                {channelMembers[member.name].is_admin ? <CrownIcon fill="#FFC53D" width={16} height={16} /> : null}
                            </View>
                            <Text className='text-sm text-muted-foreground'>{member.name}</Text>
                        </View>
                    </View>
                </Pressable>
            </View>
        </ReanimatedSwipeable>
    )
}

export default ChannelMemberRow