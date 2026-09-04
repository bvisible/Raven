import { Link, router, Stack, useLocalSearchParams } from 'expo-router';
import { Button } from '@components/nativewindui/Button';
import { Text } from '@components/nativewindui/Text';
import CrossIcon from '@assets/icons/CrossIcon.svg';
import { useColorScheme } from '@hooks/useColorScheme';
import { FormProvider, useForm } from 'react-hook-form';
import { useFrappeUpdateDoc } from "frappe-react-sdk";
import { ActivityIndicator } from '@components/nativewindui/ActivityIndicator';
import { toast } from 'sonner-native';
import { useCurrentChannelData } from '@hooks/useCurrentChannelData';
import EditChannelBaseDetailsForm, { EditChannelDetailsForm } from '@components/features/channel-settings/BaseDetails/EditChannelBaseDetailsForm';
import { Platform, View } from 'react-native';
import CommonErrorBoundary from '@components/common/CommonErrorBoundary';
import { TouchableOpacity } from 'react-native-gesture-handler';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from 'react-i18next';

export default function EditChannelDetails() {

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const { colors } = useColorScheme()

    const { id: currentChannelID } = useLocalSearchParams()
    const { channel } = useCurrentChannelData(currentChannelID as string ?? '')
    const currentChannelName = channel?.channelData.channel_name
    const currentChannelDescription = channel?.channelData.channel_description

    const methods = useForm<EditChannelDetailsForm>({
        defaultValues: {
            channel_name: currentChannelName,
            channel_description: currentChannelDescription,
        }
    })

    const { handleSubmit } = methods
    const { updateDoc, error, loading: updatingChannel } = useFrappeUpdateDoc()

    const onSubmit = async (data: EditChannelDetailsForm) => {
        return updateDoc("Raven Channel", currentChannelID as string, {
            channel_name: data.channel_name ? data.channel_name : currentChannelName,
            channel_description: data.channel_description ? data.channel_description : currentChannelDescription,
        }).then(() => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.success(t('channels.channelUpdated'))
            router.back()
        }).catch((err) => {
            console.error(err)
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('channels.channelUpdateFailed'))
        })
    }

    return <>
        <Stack.Screen options={{
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            title: t('channels.editChannelDetails'),
            headerStyle: { backgroundColor: colors.background },
            headerLeft: Platform.OS === 'ios' ? () => {
                return (
                    <Link asChild href="../" relativeToDirectory>
                        <Button variant="plain" className="ios:px-0" hitSlop={10}>
                            <CrossIcon color={colors.foreground} height={24} width={24} />
                        </Button>
                    </Link>
                )
            } : undefined,
            headerRight() {
                return (
                    <TouchableOpacity className="ios:px-0"
                        onPress={handleSubmit(onSubmit)}
                        disabled={updatingChannel}>
                        {updatingChannel ?
                            <ActivityIndicator size="small" color={colors.primary} /> :
                            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                            <Text className="text-primary font-medium dark:text-secondary">{t('common.save')}</Text>}
                    </TouchableOpacity>
                )
            },
        }} />
        <View className="flex-1 bg-background">
            <FormProvider {...methods}>
                <EditChannelBaseDetailsForm />
            </FormProvider>
        </View>
    </>
}

export const ErrorBoundary = CommonErrorBoundary