import { ErrorText, HelperText, Label } from '@/components/common/Form'
import { Loader } from '@/components/common/Loader'
import { HStack, Stack } from '@/components/layout/Stack'
import { RavenBot } from '@/types/RavenBot/RavenBot'
import { CheckCircledIcon, CrossCircledIcon } from '@radix-ui/react-icons'
import { Box, Button, Card, Checkbox, Dialog, Flex, Heading, Select, Separator, Text, TextField, Tooltip } from '@radix-ui/themes'
import { useFrappeGetCall, useFrappePostCall } from 'frappe-react-sdk'
import { useState } from 'react'
import { Controller, useFormContext } from 'react-hook-form'
import { BiInfoCircle } from 'react-icons/bi'
import { toast } from 'sonner'

type Props = {}

// Define types for model compatibility test results
interface ModelCompatibilityResult {
    status: 'not_tested' | 'success' | 'warning' | 'error';
    message: string;
    tool_support: boolean;
    details: string;
}

const AIFeaturesBotForm = (props: Props) => {
    const { register, control, formState: { errors }, watch, getValues } = useFormContext<RavenBot>()
    const [isTesting, setIsTesting] = useState(false)
    const [showTestResults, setShowTestResults] = useState(false)
    const [modelTestResult, setModelTestResult] = useState<ModelCompatibilityResult | null>(null)

    const isAiBot = watch('is_ai_bot')
    const modelProvider = watch('model_provider')
    const modelName = watch('model_name')
    const enableLocalRAG = watch('enable_local_rag')
    const openAIAssistantID = watch('openai_assistant_id')
    
    // Hook to call the model compatibility test API
    const { call: testModelCompatibility } = useFrappePostCall('raven.api.ai_features.test_model_compatibility')

    // Function to test model compatibility
    const handleTestModel = async () => {
        const currentProvider = getValues('model_provider')
        const currentModelName = getValues('model_name')
        
        if (!currentModelName) {
            toast.error("Please enter a model name to test")
            return
        }
        
        setIsTesting(true)
        
        try {
            const result = await testModelCompatibility({
                provider: currentProvider,
                model_name: currentModelName
            })
            
            // Log the result for debugging
            console.log("Model compatibility test result:", result)
            
            // Process the result
            if (result && typeof result === 'object') {
                // Handle the Frappe API response format
                const processedResult = result.message && typeof result.message === 'object' 
                    ? result.message  // Frappe API sometimes wraps the response in a message property
                    : result
                    
                setModelTestResult(processedResult as ModelCompatibilityResult)
                setShowTestResults(true)
            } else {
                toast.error("Received invalid response format from server")
            }
        } catch (error) {
            console.error("Error testing model compatibility:", error)
            toast.error("Error testing model compatibility")
        } finally {
            setIsTesting(false)
        }
    }

    return (
        <Stack gap='4'>
            
            <Stack maxWidth={'480px'}>
                <Label htmlFor='model_provider'>Model Provider</Label>
                <Controller
                    control={control}
                    name='model_provider'
                    render={({ field }) => (
                        <Select.Root
                            value={field.value || ''}
                            onValueChange={(value) => {
                                // When selecting "LocalLLM", get the provider type from settings
                                if (value === "LocalLLM") {
                                    // The actual provider type will be determined at runtime from settings
                                    field.onChange(value);
                                } else {
                                    field.onChange(value);
                                }
                            }}
                        >
                            <Select.Trigger id='model_provider' />
                            <Select.Content>
                                <Select.Item value="OpenAI">OpenAI (Cloud)</Select.Item>
                                <Select.Item value="LocalLLM">Local LLM</Select.Item>
                            </Select.Content>
                        </Select.Root>
                    )}
                />
                <HelperText>
                    Select the model provider for this agent. OpenAI uses cloud-based models, while Local LLM uses the provider configured in LLM Settings.
                </HelperText>
            </Stack>
            
            <Stack maxWidth={'480px'}>
                <Flex align="center" justify="between">
                    <Label htmlFor='model_name'>Model Name</Label>
                    <Button 
                        size="1" 
                        variant="soft" 
                        onClick={handleTestModel} 
                        disabled={isTesting || !modelName}
                    >
                        {isTesting ? <Loader className="mr-1" size={14} /> : null}
                        {isTesting ? "Testing..." : "Test Tool Support"}
                    </Button>
                </Flex>
                
                <TextField.Root
                    id='model_name'
                    {...register('model_name')}
                    placeholder={
                        modelProvider === 'OpenAI' ? 'gpt-4o' : 
                        modelProvider === 'LocalLLM' ? 'llama3-8b or other model name' : 
                        'llama3-8b'
                    }
                    aria-invalid={errors.model_name ? 'true' : 'false'}
                />
                <HelperText>
                    {modelProvider === 'OpenAI' ? 
                        'For OpenAI, use model names like "gpt-4o", "gpt-4-turbo", or "gpt-3.5-turbo".' : 
                        modelProvider === 'LocalLLM' ? 
                        'For Local LLM, enter the name of the model as it appears in your configured provider (LM Studio, Ollama, etc.).' :
                        'For specific local providers, use the name of the model as it appears in that provider.'}
                </HelperText>
                {errors.model_name && <ErrorText>{errors.model_name?.message}</ErrorText>}
            </Stack>
            
            {/* Test Results Dialog */}
            <Dialog.Root open={showTestResults} onOpenChange={setShowTestResults}>
                <Dialog.Content size="3">
                    <Dialog.Title>Model Compatibility Test Results</Dialog.Title>
                    <Dialog.Description>
                        Test results for model {modelName} with {modelProvider}
                    </Dialog.Description>
                    
                    {/* Main results card */}
                    {modelTestResult && (
                        <Card size="1" className="mt-2 mb-2">
                            <Flex direction="column" gap="2">
                                <Flex align="center" gap="2">
                                    {modelTestResult.status === 'success' ? (
                                        <CheckCircledIcon className="text-green-500" />
                                    ) : modelTestResult.status === 'error' ? (
                                        <CrossCircledIcon className="text-red-500" />
                                    ) : (
                                        <BiInfoCircle className="text-yellow-500" />
                                    )}
                                    <Text size="2" weight="bold">Tool Support: </Text>
                                    <Text>
                                        {modelTestResult.tool_support ? 
                                            "Compatible with SDK Agent tools" : 
                                            "Not fully compatible with SDK Agent tools"}
                                    </Text>
                                </Flex>
                                
                                <Text size="2" weight="bold">Result:</Text>
                                <Text size="2">{modelTestResult.message}</Text>
                                
                                {modelTestResult.details && (
                                    <>
                                        <Text size="2" weight="bold" mt="1">Details:</Text>
                                        <Text size="2">{modelTestResult.details}</Text>
                                    </>
                                )}
                                
                                {/* Special callout for recommendations */}
                                {!modelTestResult.tool_support && (
                                    <Card variant="classic" color="amber" size="1" mt="2">
                                        <Flex direction="column" gap="1">
                                            <Text weight="bold" size="2">Recommendation:</Text>
                                            <Text size="2">
                                                This model doesn't seem to fully support tool calling, which is needed for the SDK Agent to work properly.
                                                For local LLMs, we recommend models like Llama 3 (llama3) or Mistral models with "instruct" in their name.
                                            </Text>
                                            <Text size="2" mt="1">
                                                You can still use this model with our direct API implementation, but some advanced features may not work.
                                            </Text>
                                        </Flex>
                                    </Card>
                                )}
                            </Flex>
                        </Card>
                    )}
                    
                    <Flex gap="3" mt="4" justify="end">
                        <Dialog.Close>
                            <Button variant="soft" color="gray">Close</Button>
                        </Dialog.Close>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>
            
            <HStack gap='8'>
                <ModelSelector />
                <ReasoningEffortSelector />
            </HStack>
            <Separator className='w-full' />
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
            <Heading as='h5' size='2' className='not-cal' weight='medium'>Tools</Heading>
            
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
                        <Tooltip content='Enable document search and question-answering'>
                            <span className='text-gray-11 -mb-1'>
                                <BiInfoCircle size={16} />
                            </span>
                        </Tooltip>
                    </HStack>
                </Text>
                <HelperText>
                    Enable this if you want the bot to be able to read PDF files and other documents.
                    <br /><br />
                    File search enables the agent with knowledge from files that you upload.
                </HelperText>
            </Stack>
            
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
                        <Tooltip content='Enable code execution for data processing'>
                            <span className='text-gray-11 -mb-1'>
                                <BiInfoCircle size={16} />
                            </span>
                        </Tooltip>
                    </HStack>
                </Text>
                <HelperText>
                    Enable this if you want the bot to be able to process files like Excel sheets or data from Insights.
                </HelperText>
            </Stack>
            
            <Separator className='w-full' />
            <Heading as='h5' size='2' className='not-cal' weight='medium'>RAG (Retrieval-Augmented Generation) Settings</Heading>

            {/* Only show RAG options if file search is enabled */}
            {watch('enable_file_search') && (
                <>
                    <Stack maxWidth={'560px'}>
                        <Text as="label" size="2">
                            <HStack align='center'>
                                <Controller
                                    control={control}
                                    name='enable_local_rag'
                                    defaultValue={1}
                                    render={({ field }) => (
                                        <Checkbox
                                            checked={field.value ? true : false}
                                            onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                        />
                                    )} />
                                <span>Use Local Vector Database</span>
                                <Tooltip content='Use local instead of cloud-based vector storage'>
                                    <span className='text-gray-11 -mb-1'>
                                        <BiInfoCircle size={16} />
                                    </span>
                                </Tooltip>
                            </HStack>
                        </Text>
                        <HelperText>
                            When enabled (recommended), document content will be stored and searched in a local vector database instead of OpenAI's cloud storage.
                            Local storage provides better privacy, reduced costs, and works with all model providers.
                        </HelperText>
                    </Stack>
                    
                    {/* Local RAG Provider selection */}
                    {enableLocalRAG && (
                        <>
                            <Stack maxWidth={'480px'}>
                                <Label htmlFor='local_rag_provider'>Vector Database</Label>
                                <Controller
                                    control={control}
                                    name='local_rag_provider'
                                    render={({ field }) => (
                                        <Select.Root
                                            value={field.value || 'Chroma'}
                                            onValueChange={field.onChange}
                                        >
                                            <Select.Trigger id='local_rag_provider' />
                                            <Select.Content>
                                                <Select.Item value="Chroma">ChromaDB</Select.Item>
                                                <Select.Item value="FAISS">FAISS</Select.Item>
                                                <Select.Item value="Weaviate">Weaviate</Select.Item>
                                                <Select.Item value="LLMEnhanced">LLM-Enhanced</Select.Item>
                                            </Select.Content>
                                        </Select.Root>
                                    )}
                                />
                                <HelperText>
                                    ChromaDB is recommended for most use cases, FAISS for larger document collections,
                                    and Weaviate for more complex semantic search requirements. LLM-Enhanced uses ChromaDB with AI-powered query enhancement.
                                </HelperText>
                            </Stack>

                            <Stack maxWidth={'560px'}>
                                <Text as="label" size="2">
                                    <HStack align='center'>
                                        <Controller
                                            control={control}
                                            name='use_llm_enhanced'
                                            defaultValue={1}
                                            render={({ field }) => (
                                                <Checkbox
                                                    checked={field.value ? true : false}
                                                    onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                                />
                                            )} />
                                        <span>Use LLM for Query Enhancement</span>
                                        <Tooltip content='More language-agnostic search using LLM'>
                                            <span className='text-gray-11 -mb-1'>
                                                <BiInfoCircle size={16} />
                                            </span>
                                        </Tooltip>
                                    </HStack>
                                </Text>
                                <HelperText>
                                    Use the configured LLM to understand and enhance search queries in any language.
                                </HelperText>
                            </Stack>
                        </>
                    )}
                    
                    {/* OpenAI Vector Store IDs - only show if using OpenAI provider and not using local RAG */}
                    {modelProvider === 'OpenAI' && !enableLocalRAG && (
                        <Stack maxWidth={'480px'}>
                            <Label htmlFor='vector_store_ids'>OpenAI Vector Store IDs</Label>
                            <TextField.Root
                                id='vector_store_ids'
                                {...register('vector_store_ids')}
                                placeholder="vs-abc123,vs-def456"
                                aria-invalid={errors.vector_store_ids ? 'true' : 'false'}
                            />
                            <HelperText>
                                Comma-separated list of OpenAI vector store IDs (vs-*). Required for document search with OpenAI.
                            </HelperText>
                            {errors.vector_store_ids && <ErrorText>{errors.vector_store_ids?.message}</ErrorText>}
                        </Stack>
                    )}
                </>
            )}
            
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
            
            <Stack maxWidth={'480px'}>
                <Label htmlFor='agent_settings'>Agent Settings (JSON)</Label>
                <TextField.Root
                    id='agent_settings'
                    {...register('agent_settings')}
                    placeholder='{"temperature": 0.7, "max_tokens": 1000}'
                    aria-invalid={errors.agent_settings ? 'true' : 'false'}
                />
                <HelperText>
                    Optional JSON configuration for advanced agent settings. This will be passed to the model provider.
                </HelperText>
                {errors.agent_settings && <ErrorText>{errors.agent_settings?.message}</ErrorText>}
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