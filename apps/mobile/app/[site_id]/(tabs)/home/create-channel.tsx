import CreateChannelForm, { ChannelCreationForm } from '@components/features/channels/CreateChannel/CreateChannelForm';
import { Link, Stack } from 'expo-router';
import { Button } from '@components/nativewindui/Button';
import { Text } from '@components/nativewindui/Text';
import CrossIcon from '@assets/icons/CrossIcon.svg';
import { useColorScheme } from '@hooks/useColorScheme';
import { FormProvider, useForm } from 'react-hook-form';
import { useFrappeCreateDoc } from "frappe-react-sdk";
import { ActivityIndicator } from '@components/nativewindui/ActivityIndicator';
import { useGetCurrentWorkspace } from '@hooks/useGetCurrentWorkspace';
import { toast } from 'sonner-native';
import { useRouteToChannel } from '@hooks/useRouting';
import { TouchableOpacity } from 'react-native-gesture-handler';
import { Platform } from 'react-native';
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): react-i18next import, no upstream equivalent.
import { useTranslation } from 'react-i18next';

//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
export default function CreateChannel() {
    const { t } = useTranslation();
    const { colors } = useColorScheme()
    const methods = useForm<ChannelCreationForm>({
        defaultValues: {
            type: 'Public',
            channel_name: '',
            channel_description: ''
        }
    })

    const goToChannel = useRouteToChannel()
    const { workspace } = useGetCurrentWorkspace()

    const { handleSubmit, reset: resetForm } = methods
    const { createDoc, error, loading: creatingChannel, reset: resetCreateHook } = useFrappeCreateDoc()

    const reset = () => {
        resetCreateHook()
        resetForm()
    }

    const onSubmit = async (data: ChannelCreationForm) => {
        return createDoc('Raven Channel', {
            ...data,
            workspace: workspace
        }).then(result => {
            if (result) {
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                toast.success(t('channels.channelCreated'), result)
                // Navigate to channel
                goToChannel(result.name, 'replace')
                reset()
                resetForm()
            }
        }).catch(err => {
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            toast.error(t('channels.channelCreationFailed'), err)
        })
    }

    return <>
        <Stack.Screen options={{
            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
            title: t('channels.addChannel'),
            headerLeft: Platform.OS === 'ios' ? () => {
                return (
                    <Link asChild href="../" relativeToDirectory>
                        <Button variant="plain" className="ios:px-0" hitSlop={10}>
                            <CrossIcon color={colors.icon} height={24} width={24} />
                        </Button>
                    </Link>
                )
            } : undefined,
            headerRight() {
                return (
                    <TouchableOpacity className="ios:px-0"
                        onPress={handleSubmit(onSubmit)}
                        disabled={creatingChannel}>
                        {creatingChannel ?
                            <ActivityIndicator size="small" color={colors.primary} /> :
                            //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                            <Text className="text-primary font-medium dark:text-secondary">{t('common.add')}</Text>}
                    </TouchableOpacity>
                )
            },
        }} />
        <FormProvider {...methods}>
            <CreateChannelForm />
        </FormProvider>
    </>
}