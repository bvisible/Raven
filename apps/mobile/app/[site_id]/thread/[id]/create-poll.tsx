import { Stack, useLocalSearchParams } from 'expo-router';
import { FormProvider } from 'react-hook-form';
import { useColorScheme } from '@hooks/useColorScheme';
import CreatePollForm from '@components/features/polls/CreatePollForm';
import { CloseCreatePollButton, PollCreateButton, useCreatePoll } from '@components/features/polls/CreatePollComponents';
import { Platform } from 'react-native';

export default function CreatePollPage() {

    const { colors } = useColorScheme()

    const { id: channelID } = useLocalSearchParams()

    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useCreatePoll now also returns t. The poll button is
    //// rendered by a plain function (not a component), so it cannot call useTranslation itself -
    //// t is threaded through as a prop instead.
    const { methods, onPress, creatingPoll, t } = useCreatePoll(channelID as string)

    return (
        <>
            <Stack.Screen options={{
                headerStyle: { backgroundColor: colors.background },
                headerLeft: Platform.OS === 'ios' ? () => <CloseCreatePollButton /> : undefined,
                //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json.
                headerTitle: t('polls.createPoll'),
                headerRight() {
                    return (
                        //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): t passed down to PollCreateButton (see above).
                        <PollCreateButton onPress={onPress} isCreating={creatingPoll} t={t} />
                    )
                },
            }} />

            <FormProvider {...methods}>
                <CreatePollForm />
            </FormProvider>
        </>
    )
} 