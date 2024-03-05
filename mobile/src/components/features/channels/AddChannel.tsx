import { IonButton, IonButtons, IonContent, ToastOptions, IonHeader, IonInput, IonItem, IonItemDivider, IonItemGroup, IonLabel, IonList, IonModal, IonRadio, IonRadioGroup, IonText, IonTextarea, IonTitle, IonToolbar, useIonToast } from "@ionic/react";
import { useFrappeCreateDoc } from "frappe-react-sdk";
import { useCallback, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { BiGlobe, BiHash, BiLockAlt } from "react-icons/bi";
import { useHistory } from "react-router-dom";
import { ErrorBanner } from "../../layout";
import { useChannelList } from "@/utils/channel/ChannelListProvider";

interface AddChannelProps {
    presentingElement: HTMLElement | undefined,
    isOpen: boolean,
    onDismiss: VoidFunction
}

type CreateChannelInputs = {
    channel_name: string,
    channel_description: string
    channel_type: 'Private' | 'Public' | 'Open'
}

export const AddChannel = ({ presentingElement, isOpen, onDismiss }: AddChannelProps) => {

    const modal = useRef<HTMLIonModalElement>(null)
    const { register, control, handleSubmit, formState: { errors }, setValue, reset: resetForm } = useForm<CreateChannelInputs>()
    const [channelType, setChannelType] = useState<CreateChannelInputs['channel_type']>('Public')

    const { createDoc, error: channelCreationError, reset } = useFrappeCreateDoc()

    const { mutate } = useChannelList()

    const [present] = useIonToast()

    const presentToast = (message: string, color: ToastOptions['color']) => {
        present({
            message,
            duration: 1500,
            color,
            position: 'bottom',
        })
    }

    const history = useHistory()

    const onSubmit = (data: CreateChannelInputs) => {
        let name = data.channel_name
        createDoc('Raven Channel', {
            channel_name: data.channel_name,
            channel_description: data.channel_description,
            type: channelType
        }).catch((err) => {
            if (err.httpStatus === 409) {
                presentToast("Channel name already exists.", 'danger')
            }
            else {
                presentToast("Error while creating the channel.", 'danger')
            }
        }).then((result) => {
            name = result.name
            resetForm()
            return mutate()
        }).then(() => {
            presentToast("Channel created successfully.", 'success')
            onDismiss()
            history.push(`channel/${name}`)
        })
    }


    const handleNameChange = useCallback((value?: string | null) => {
        setValue('channel_name', value?.toLowerCase().replace(' ', '-') ?? '')
    }, [setValue])


    return (
        <IonModal ref={modal} onDidDismiss={onDismiss} isOpen={isOpen} presentingElement={presentingElement}>
            <IonHeader>
                <IonToolbar>
                    <IonButtons slot="start">
                        <IonButton color={'medium'} onClick={onDismiss}>Annuler</IonButton>
                    </IonButtons>
                    <IonTitle>Créer un canal</IonTitle>
                    <IonButtons slot="end">
                        <IonButton color={'primary'} onClick={handleSubmit(onSubmit)}>Créer</IonButton>
                    </IonButtons>
                </IonToolbar>
            </IonHeader>
            <IonContent>
                <ErrorBanner error={channelCreationError} />
                <form onSubmit={handleSubmit(onSubmit)}>
                    <IonList>
                        <IonItemGroup>
                            <IonItemDivider className="py-1">
                                <IonLabel>Nom du canal</IonLabel>
                            </IonItemDivider>
                            <IonItem lines='none' className="pb-2">
                                <div slot='start'>
                                    {channelType === 'Public' && <BiHash size='16' color='var(--ion-color-medium)' />}
                                    {channelType === 'Private' && <BiLockAlt size='16' color='var(--ion-color-medium)' />}
                                    {channelType === 'Open' && <BiGlobe size='16' color='var(--ion-color-medium)' />}
                                </div>
                                <Controller
                                    name='channel_name'
                                    control={control}
                                    rules={{
                                        required: "Le nom du canal est obligatoire",
                                        maxLength: 50,
                                        pattern: {
                                            // no special characters allowed
                                            // cannot start with a space
                                            value: /^[a-zA-Z0-9][a-zA-Z0-9-]*$/,
                                            message: "Le nom du canal ne peut contenir que des lettres, des chiffres et des traits d'union."
                                        }
                                    }}
                                    render={({ field }) => <IonInput
                                        required
                                        maxlength={50}
                                        autoCapitalize="off"
                                        value={field.value}
                                        placeholder='exemple : action-seo, compta-24'
                                        className={!!errors?.channel_name ? 'ion-invalid ion-touched' : ''}
                                        aria-label="Nom du canal"
                                        errorText={errors?.channel_name?.message}
                                        onIonInput={(e) => handleNameChange(e.target.value as string)}
                                    />}
                                />
                            </IonItem>
                        </IonItemGroup>

                        <IonItemGroup>
                            <IonItemDivider className="py-1">
                                <IonLabel>Description</IonLabel>
                            </IonItemDivider>
                            <IonItem lines='none'>
                                <IonTextarea
                                    {...register("channel_description")}
                                    placeholder="Décrivez l'objectif de ce canal"
                                    className={errors?.channel_description ? 'ion-invalid' : ''}
                                    aria-label="Description du canal (optionnel)"
                                    autoGrow
                                    rows={4}
                                />
                            </IonItem>
                        </IonItemGroup>
                        <IonItemGroup>
                            <IonItemDivider className="py-1">
                                <IonLabel>Type de canal</IonLabel>
                            </IonItemDivider>
                            <IonRadioGroup value={channelType} onIonChange={e => setChannelType(e.detail.value)}>
                                <IonItem>
                                    <div slot='start'>
                                        <BiHash size='16' color='var(--ion-color-dark)' />
                                    </div>
                                    <IonRadio mode='md' className="h-8" labelPlacement="start" justify="space-between" value="Public">
                                        Public
                                    </IonRadio>
                                </IonItem>
                                <IonItem>
                                    <div slot='start'>
                                        <BiLockAlt size='16' color='var(--ion-color-dark)' />
                                    </div>
                                    <IonRadio mode='md' className="h-8" labelPlacement="start" justify="space-between" value="Private">
                                        Private
                                    </IonRadio>
                                </IonItem>

                                <IonItem>
                                    <div slot='start'>
                                        <BiGlobe size='16' color='var(--ion-color-dark)' />
                                    </div>
                                    <IonRadio mode='md' className="h-8" labelPlacement="start" justify="space-between" value="Open">
                                        Open
                                    </IonRadio>
                                </IonItem>

                                <IonItem lines='none' className="pt-2">
                                    {channelType === 'Public' && <IonText className="text-sm" color='medium'>Lorsqu'un canal est défini comme public, tout le monde peut s'y inscrire et lire les messages, mais seuls les membres peuvent publier des messages.</IonText>}
                                    {channelType === 'Private' && <IonText className="text-sm" color='medium'>Lorsqu'un canal est défini comme privé, il ne peut être consulté ou rejoint que sur invitation.</IonText>}
                                    {channelType === 'Open' && <IonText className="text-sm" color='medium'>Lorsqu'un canal est ouvert, tout le monde en est membre.</IonText>}
                                </IonItem>

                            </IonRadioGroup>

                        </IonItemGroup>

                    </IonList>
                </form>
            </IonContent>
        </IonModal>
    )
}