import { useFrappeCreateDoc } from 'frappe-react-sdk'
import { ChangeEvent, useCallback, useMemo, useState } from 'react'
import { Controller, FormProvider, useForm } from 'react-hook-form'
import { BiGlobe, BiHash, BiLockAlt } from 'react-icons/bi'
import { useNavigate } from 'react-router-dom'
import { ErrorBanner } from '../../layout/AlertBanner'
import { Box, Button, Dialog, Flex, IconButton, RadioGroup, Text, TextArea, TextField } from '@radix-ui/themes'
import { BiPlus } from 'react-icons/bi'
import { ErrorText, HelperText, Label } from '@/components/common/Form'
import { Loader } from '@/components/common/Loader'
import { DIALOG_CONTENT_CLASS } from '@/utils/layout/dialog'
import { useToast } from '@/hooks/useToast'

interface ChannelCreationForm {
    channel_name: string,
    channel_description: string,
    type: 'Public' | 'Private' | 'Open'
}

export const CreateChannelButton = ({ updateChannelList }: { updateChannelList: VoidFunction }) => {
    let navigate = useNavigate()
    const methods = useForm<ChannelCreationForm>({
        defaultValues: {
            type: 'Public',
            channel_name: '',
            channel_description: ''
        }
    })
    const { register, handleSubmit, watch, formState: { errors }, control, setValue, reset: resetForm } = methods

    const { createDoc, error: channelCreationError, loading: creatingChannel, reset: resetCreateHook } = useFrappeCreateDoc()
    const [isOpen, setIsOpen] = useState(false)

    const onClose = (channel_name?: string) => {
        if (channel_name) {
            // Update channel list when name is provided.
            // Also navigate to new channel
            updateChannelList()
            navigate(`/channel/${channel_name}`)
        }
        setIsOpen(false)

        reset()
    }

    const reset = () => {
        resetCreateHook()
        resetForm()
    }

    const onOpenChange = (open: boolean) => {
        setIsOpen(open)
        reset()
    }


    const { toast } = useToast()

    const channelType = watch('type')

    const onSubmit = (data: ChannelCreationForm) => {
        createDoc('Raven Channel', data).then(result => {
            if (result) {
                toast({
                    title: "Channel Created",
                    variant: "success",
                    duration: 1000,
                })
                onClose(result.name)
            }
        })
    }

    const handleNameChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
        setValue('channel_name', event.target.value?.toLowerCase().replace(' ', '-'))
    }, [setValue])

    const { channelIcon, header, helperText } = useMemo(() => {
        switch (channelType) {
            case 'Private':
                return {
                    channelIcon: <BiLockAlt />,
                    header: 'Créer un canal privé',
                    helperText: 'Lorsqu\'un canal est défini comme privé, il ne peut être consulté ou rejoint que sur invitation.'
                }
            case 'Open':
                return {
                    channelIcon: <BiGlobe />,
                    header: 'Créer un canal ouvert',
                    helperText: 'Lorsqu\'un canal est ouvert, tout le monde en est membre.'
                }
            default:
                return {
                    channelIcon: <BiHash />,
                    header: 'Créer un canal public',
                    helperText: 'Lorsqu\'un canal est défini comme public, tout le monde peut s\'y inscrire et lire les messages, mais seuls les membres peuvent envoyer des messages.'
                }
        }
    }, [channelType])

    return <Dialog.Root open={isOpen} onOpenChange={onOpenChange}>
        <Dialog.Trigger>
            <IconButton variant='ghost' size='1' color='gray' aria-label='Create Channel' className='h-[18px]' title='Create Channel'>
                <BiPlus className='text-slate-12 mt-0.5' />
            </IconButton>
        </Dialog.Trigger>
        <Dialog.Content className={DIALOG_CONTENT_CLASS}>
            <Dialog.Title>
                {header}
            </Dialog.Title>
            <Dialog.Description size='2'>
                Les canaux permettent à votre équipe de communiquer. Ils sont plus efficaces lorsqu'ils sont organisés autour d'un thème - #développement, par exemple.
            </Dialog.Description>
            <FormProvider {...methods}>
                <form onSubmit={handleSubmit(onSubmit)}>
                    <Flex direction='column' gap='4' py='4'>
                        <ErrorBanner error={channelCreationError} />
                        <Box>
                            <Label htmlFor='channel_name' isRequired>Nom</Label>
                            <Controller
                                name='channel_name'
                                control={control}
                                rules={{
                                    required: "Veuillez ajouter un nom de canal",
                                    maxLength: {
                                        value: 50,
                                        message: "Le nom du canal ne peut pas comporter plus de 50 caractères."
                                    },
                                    minLength: {
                                        value: 3,
                                        message: "Le nom du canal ne peut être inférieur à 3 caractères."
                                    },
                                    pattern: {
                                        // no special characters allowed
                                        // cannot start with a space
                                        value: /^[a-zA-Z0-9][a-zA-Z0-9-]*$/,
                                        message: "Le nom du canal ne peut contenir que des lettres, des chiffres et des traits d'union."
                                    }
                                }}
                                render={({ field, fieldState: { error } }) => (
                                    <TextField.Root>
                                        <TextField.Slot>
                                            {channelIcon}
                                        </TextField.Slot>
                                        <TextField.Input
                                            maxLength={50}
                                            required
                                            autoFocus
                                            placeholder='exemple : action-seo, compta-24'
                                            color={error ? 'red' : undefined}
                                            {...field}
                                            aria-invalid={error ? 'true' : 'false'}
                                            onChange={handleNameChange}
                                        />
                                        <TextField.Slot>
                                            <Text size='2' weight='light' color='gray'>{50 - field.value.length}</Text>
                                        </TextField.Slot>
                                    </TextField.Root>
                                )}
                            />
                            {errors?.channel_name && <ErrorText>{errors.channel_name?.message}</ErrorText>}
                        </Box>

                        <Box>
                            <Label htmlFor='channel_description'>Description <Text as='span' weight='light'>(facultatif)</Text></Label>
                            <TextArea
                                maxLength={140}
                                id='channel_description'
                                placeholder='Décrivez l objectif de ce canal'
                                {...register('channel_description', {
                                    maxLength: {
                                        value: 140,
                                        message: "La description du canal ne doit pas dépasser 140 caractères."
                                    }
                                })}
                                aria-invalid={errors.channel_description ? 'true' : 'false'}
                            />
                            <HelperText>What is this channel about?</HelperText>
                            {errors?.channel_description && <ErrorText>{errors.channel_description?.message}</ErrorText>}
                        </Box>
                        <Flex gap='2' direction='column'>
                            <Label htmlFor='channel_type'>Channel Type</Label>
                            <Controller
                                name='type'
                                control={control}
                                render={({ field }) => (
                                    <RadioGroup.Root
                                        defaultValue="1"
                                        variant='soft'
                                        id='channel_type'
                                        value={field.value}
                                        onValueChange={field.onChange}>
                                        <Flex gap="4">
                                            <Text as="label" size="2">
                                                <Flex gap="2">
                                                    <RadioGroup.Item value="Public" /> Public
                                                </Flex>
                                            </Text>
                                            <Text as="label" size="2">
                                                <Flex gap="2">
                                                    <RadioGroup.Item value="Private" /> Private
                                                </Flex>
                                            </Text>
                                            <Text as="label" size="2">
                                                <Flex gap="2">
                                                    <RadioGroup.Item value="Open" /> Open
                                                </Flex>
                                            </Text>
                                        </Flex>
                                    </RadioGroup.Root>
                                )}
                            />
                            {/* Added min height to avoid layout shift when two lines of text are shown */}
                            <Text size='1' weight='light' className='min-h-[2rem]'>
                                {helperText}
                            </Text>
                        </Flex>
                    </Flex>
                    <Flex gap="3" mt="4" justify="end">
                        <Dialog.Close disabled={creatingChannel}>
                            <Button variant="soft" color="gray">
                                Annuler
                            </Button>
                        </Dialog.Close>
                        <Button type='submit' disabled={creatingChannel}>
                            {creatingChannel && <Loader />}
                            {creatingChannel ? "Enregistrement" : "Enregistrer"}
                        </Button>
                    </Flex>
                </form>
            </FormProvider>
        </Dialog.Content>
    </Dialog.Root>
}