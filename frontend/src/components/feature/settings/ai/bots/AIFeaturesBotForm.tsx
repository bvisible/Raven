import { ErrorText, HelperText, Label } from '@/components/common/Form'
import { HStack, Stack } from '@/components/layout/Stack'
import useRavenSettings from '@/hooks/fetchers/useRavenSettings'
import { RavenBot } from '@/types/RavenBot/RavenBot'
import { Box, Button, Checkbox, Heading, Select, Separator, Text, TextField } from '@radix-ui/themes'
import { useFrappeGetCall, useFrappePostCall } from 'frappe-react-sdk'
import { Controller, useFormContext } from 'react-hook-form'
import { toast } from 'react-toastify'

type Props = {}

const AIFeaturesBotForm = (props: Props) => {
    const { register, control, formState: { errors }, watch } = useFormContext<RavenBot>()
    const { ravenSettings } = useRavenSettings()
    
    const openAIAssistantID = watch('openai_assistant_id')
    const modelProvider = watch('model_provider')
    const useLocalRag = watch('use_local_rag')
    const openAIVectorStoreID = watch('openai_vector_store_id')
    
    // Determining which provider to use
    const getAvailableProviders = () => {
        const providers = [];
        if (ravenSettings?.enable_openai_services) {
            providers.push({ value: 'openai', label: 'OpenAI' });
        }
        if (ravenSettings?.enable_local_llm) {
            // Use the provider configured in the settings
            const localProvider = ravenSettings.local_llm_provider || 'LM Studio';
            providers.push({ value: 'local', label: `Local LLM (${localProvider})` });
        }
        return providers;
    }

    const { call: testModelCompatibility } = useFrappePostCall('raven.api.ai_features.test_model_compatibility')

    return (
        <Stack gap='4'>
            {/* Selection of LLM provider */}
            <Stack maxWidth={'480px'}>
                <Label htmlFor='model_provider'>Model Provider</Label>
                <Controller
                    control={control}
                    name='model_provider'
                    render={({ field }) => (
                        <Select.Root
                            value={field.value || 'openai'}
                            onValueChange={field.onChange}
                        >
                            <Select.Trigger />
                            <Select.Content>
                                {getAvailableProviders().map(provider => (
                                    <Select.Item key={provider.value} value={provider.value}>
                                        {provider.label}
                                    </Select.Item>
                                ))}
                            </Select.Content>
                        </Select.Root>
                    )}
                />
                <HelperText>
                    Choose which LLM provider this bot should use
                </HelperText>
            </Stack>
            
            {/* If OpenAI, show the assistant ID (will be removed after migration) */}
            {modelProvider === 'openai' && (
                <Stack maxWidth={'480px'}>
                    <Box hidden={!openAIAssistantID}>
                        <Label htmlFor='openai_assistant_id'>OpenAI Assistant ID (Legacy - Will be removed)</Label>
                        <TextField.Root
                            id='openai_assistant_id'
                            {...register('openai_assistant_id')}
                            readOnly
                            placeholder="asst_*******************"
                        />
                    </Box>
                </Stack>
            )}
            
            {/* If Local LLM, show the model override */}
            {modelProvider === 'local' && (
                <Stack maxWidth={'480px'}>
                    <Label htmlFor='local_model_override'>Model Override (Optional)</Label>
                    <TextField.Root
                        id='local_model_override'
                        {...register('local_model_override')}
                        placeholder="Leave empty to use default model"
                    />
                    <HelperText>
                        Override the model for this bot (provider: {ravenSettings?.local_llm_provider})
                    </HelperText>
                </Stack>
            )}
            
            <HStack gap='8'>
                <ModelSelector />
                <ReasoningEffortSelector />
            </HStack>
            
            <Separator className='w-full' />
            
            {/* Local RAG Option */}
            <Stack maxWidth={'560px'}>
                <Text as="label" size="2">
                    <HStack align='center'>
                        <Controller
                            control={control}
                            name='use_local_rag'
                            render={({ field }) => (
                                <Checkbox
                                    checked={field.value ? true : false}
                                    onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                />
                            )} />
                        <span>Use Local RAG</span>
                    </HStack>
                </Text>
                <HelperText>
                    Enable RAG (Retrieval-Augmented Generation) with local documents instead of OpenAI Vector Store
                </HelperText>
            </Stack>
            
            {/* Configuration RAG */}
            {useLocalRag && (
                <Stack maxWidth={'480px'}>
                    <Label>RAG Settings</Label>
                    <Box>
                        <Label htmlFor='rag_similarity_threshold'>Similarity Threshold</Label>
                        <TextField.Root
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            {...register('rag_settings.similarity_threshold')}
                            defaultValue="0.7"
                        />
                    </Box>
                    <Box>
                        <Label htmlFor='rag_max_results'>Max Results</Label>
                        <TextField.Root
                            type="number"
                            min="1"
                            max="20"
                            {...register('rag_settings.max_results')}
                            defaultValue="5"
                        />
                    </Box>
                </Stack>
            )}
            
            <Stack maxWidth={'480px'}>
                <Text as="label" size="2">
                    <HStack>
                        <Controller
                            control={control}
                            name='allow_bot_to_write_documents'
                            render={({ field }) => (
                                <Checkbox
                                    checked={field.value ? true : false}
                                    onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                />
                            )} />

                        Allow Agent to Write Documents
                    </HStack>
                </Text>
                <HelperText>
                    Checking this will allow the bot to create/update/delete documents in the system.
                </HelperText>
            </Stack>
            <Separator className='w-full' />
            
            {/* File Search - Conditionnel selon use_local_rag */}
            <Stack maxWidth={'560px'}>
                <Text as="label" size="2">
                    <HStack align='center'>
                        <Controller
                            control={control}
                            name='enable_file_search'
                            render={({ field }) => (
                                <Checkbox
                                    checked={field.value ? true : false}
                                    onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                />
                            )} />
                        <span>Enable File Search</span>
                    </HStack>
                </Text>
                <HelperText>
                    {useLocalRag 
                        ? "Files will be indexed locally using the RAG system"
                        : modelProvider === 'openai' 
                            ? "Files will be uploaded to OpenAI Vector Store"
                            : "Files will be processed locally"}
                </HelperText>
            </Stack>
            
            {/* OpenAI Vector Store ID - Only if OpenAI and no local RAG */}
            {!useLocalRag && modelProvider === 'openai' && (
                <Stack maxWidth={'480px'}>
                    <Box hidden={!openAIVectorStoreID}>
                        <Label htmlFor='openai_vector_store_id'>OpenAI Vector Store ID</Label>
                        <TextField.Root
                            id='openai_vector_store_id'
                            {...register('openai_vector_store_id')}
                            readOnly
                        />
                    </Box>
                </Stack>
            )}
            
            <Separator className='w-full' />
            
            {/* Code Interpreter - only for OpenAI */}
            {modelProvider === 'openai' && (
                <Stack maxWidth={'560px'}>
                    <Text as="label" size="2">
                        <HStack align='center'>
                            <Controller
                                control={control}
                                name='enable_code_interpreter'
                                render={({ field }) => (
                                    <Checkbox
                                        checked={field.value ? true : false}
                                        onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                    />
                                )} />
                            <span>Enable Code Interpreter</span>
                        </HStack>
                    </Text>
                    <HelperText>
                        OpenAI-specific feature for processing Excel sheets and data
                    </HelperText>
                </Stack>
            )}
            
            {/* Test of model compatibility */}
            <Stack maxWidth={'480px'}>
                <Button
                    onClick={async () => {
                        const provider = modelProvider === 'local' 
                            ? ravenSettings?.local_llm_provider 
                            : 'OpenAI';
                        const model = modelProvider === 'local' 
                            ? watch('local_model_override') || 'default'
                            : watch('model') || 'gpt-4';
                            
                        const result = await testModelCompatibility({
                            provider,
                            model_name: model
                        });
                        
                        // Display results
                        toast(result.message);
                    }}
                    variant="soft"
                >
                    Test Model Compatibility
                </Button>
            </Stack>
            
            <Separator className='w-full' />
            <Heading as='h5' size='2' className='not-cal' weight='medium'>Advanced</Heading>
            <Stack maxWidth={'560px'}>
                <Text as="label" size="2">
                    <HStack align='center'>
                        <Controller
                            control={control}
                            name='debug_mode'
                            render={({ field }) => (
                                <Checkbox
                                    checked={field.value ? true : false}
                                    onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                />
                            )} />
                        <span>Enable Debug Mode</span>
                    </HStack>
                </Text>
                <HelperText>
                    If enabled, stack traces of errors will be sent as messages by the bot during runs.
                    <br />
                    This is helpful when you're testing your bots and want to know where things are going wrong.
                </HelperText>
            </Stack>

        </Stack>
    )
}

const ModelSelector = () => {

    const { data: models } = useFrappeGetCall('raven.api.ai_features.get_openai_available_models', undefined, undefined, {
        revalidateOnFocus: false,
        revalidateIfStale: false
    })
    const { control, formState: { errors }, watch } = useFormContext<RavenBot>()

    const is_ai_bot = watch('is_ai_bot')


    return <Stack maxWidth={'480px'}>
        <Box>
            <Label htmlFor='model' isRequired>Model</Label>
            <Controller control={control} name='model'
                rules={{
                    required: is_ai_bot ? true : false
                }}
                defaultValue='gpt-4o'
                render={({ field }) => (
                    <Select.Root
                        value={field.value}
                        name={field.name}
                        onValueChange={(value) => field.onChange(value)}>
                        <Select.Trigger placeholder='Select Model' className='w-full' />
                        <Select.Content>
                            {models?.message.map((model: string) => (
                                <Select.Item key={model} value={model}>{model}</Select.Item>
                            ))}
                        </Select.Content>
                    </Select.Root>
                )} />
        </Box>
        {errors.model && <ErrorText>{errors.model?.message}</ErrorText>}
        <HelperText>
            The model you select will be used to run the agent.
            <br />
            The model should be compatible with the OpenAI Assistants API. We recomment using models in the GPT-4 family for best results.
        </HelperText>
    </Stack>
}

const ReasoningEffortSelector = () => {
    const { control, watch } = useFormContext<RavenBot>()

    const model = watch('model')

    const is_ai_bot = watch('is_ai_bot')

    if (!model) return null

    if (model.startsWith("o")) {
        return <Stack maxWidth={'480px'}>
            <Box>
                <Label htmlFor='reasoning_effort' isRequired>Reasoning Effort</Label>
                <Controller control={control}
                    rules={{
                        required: model.startsWith("o") && is_ai_bot ? true : false
                    }}
                    name='reasoning_effort' render={({ field }) => (
                        <Select.Root value={field.value} name={field.name} onValueChange={(value) => field.onChange(value)}>
                            <Select.Trigger placeholder='Select Reasoning Effort' className='w-full' />
                            <Select.Content>
                                <Select.Item value='low'>Low</Select.Item>
                                <Select.Item value='medium'>Medium</Select.Item>
                                <Select.Item value='high'>High</Select.Item>
                            </Select.Content>
                        </Select.Root>
                    )} />
            </Box>
            <HelperText>
                The reasoning effort will be used to determine the depth of the reasoning process. This is only applicable for OpenAI's o-series models.
            </HelperText>
        </Stack>
    }
    return null
}

export default AIFeaturesBotForm