import { Loader } from '@/components/common/Loader'
import InstructionTemplateForm from '@/components/feature/settings/ai/InstructionTemplateForm'
import { ErrorBanner } from '@/components/layout/AlertBanner/ErrorBanner'
import PageContainer from '@/components/layout/Settings/PageContainer'
import SettingsContentContainer from '@/components/layout/Settings/SettingsContentContainer'
import SettingsPageHeader from '@/components/layout/Settings/SettingsPageHeader'
import { RavenBotInstructionTemplate } from '@/types/RavenAI/RavenBotInstructionTemplate'
import { Button } from '@radix-ui/themes'
import { useFrappeCreateDoc } from 'frappe-react-sdk'
import { FormProvider, useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'

const CreateInstructionTemplate = () => {

    const { createDoc, loading, error } = useFrappeCreateDoc<RavenBotInstructionTemplate>()

    const methods = useForm<RavenBotInstructionTemplate>({
        disabled: loading
    })

    const navigate = useNavigate()

    const onSubmit = (data: RavenBotInstructionTemplate) => {
        createDoc("Raven Bot Instruction Template", data)
            .then((doc) => {
                navigate(`../${doc.name}`)
            })
    }

    return (
        <PageContainer>
            <form onSubmit={methods.handleSubmit(onSubmit)}>
                <FormProvider {...methods}>
                    <SettingsContentContainer>
                        <SettingsPageHeader
                            title='Create an Instruction Template'
                            actions={<Button type='submit' disabled={loading}>
                                {loading && <Loader />}
                                {loading ? "Creating" : "Create"}
                            </Button>}
                            breadcrumbs={[{ label: 'Instruction Templates', href: '../' }, { label: 'New Instruction Template', href: '' }]}
                        />
                        <ErrorBanner error={error} />
                        <InstructionTemplateForm />
                    </SettingsContentContainer>
                </FormProvider>
            </form>
        </PageContainer>
    )
}

export const Component = CreateInstructionTemplate