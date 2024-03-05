import { IonSpinner, IonText } from '@ionic/react'

type Props = {
    text?: string
}

export const FullPageLoader = ({ text = "neochat est actuellement en cours de chargement. Veuillez patienter..." }: Props) => {
    return (
        <div className='h-full w-full flex justify-center items-center flex-col'>
            <IonSpinner color={'dark'} name='crescent' />
            <IonText color='medium' className='text-sm mt-3'>{text}</IonText>
        </div>
    )
}