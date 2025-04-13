import { Label, ErrorText, HelperText } from '@/components/common/Form'
import { Stack, HStack } from '@/components/layout/Stack'
import { RavenBot } from '@/types/RavenBot/RavenBot'
import { TextField, Checkbox, Text, Separator, Tooltip, Heading, Select } from '@radix-ui/themes'
import { useFormContext, Controller } from 'react-hook-form'
import { BiInfoCircle } from 'react-icons/bi'

type Props = {}

const AIFeaturesBotForm = (props: Props) => {
    const { register, control, formState: { errors }, watch } = useFormContext<RavenBot>()

    const isAiBot = watch('is_ai_bot')
    const modelProvider = watch('model_provider')
    const enableLocalRAG = watch('enable_local_rag')

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
                            onValueChange={field.onChange}
                        >
                            <Select.Trigger id='model_provider' />
                            <Select.Content>
                                <Select.Item value="OpenAI">OpenAI</Select.Item>
                                <Select.Item value="LMStudio">LM Studio</Select.Item>
                                <Select.Item value="Ollama">Ollama</Select.Item>
                                <Select.Item value="LocalAI">LocalAI</Select.Item>
                            </Select.Content>
                        </Select.Root>
                    )}
                />
                <HelperText>
                    Select the model provider for this agent. OpenAI uses cloud-based models, while other providers use local models.
                </HelperText>
            </Stack>
            
            <Stack maxWidth={'480px'}>
                <Label htmlFor='model_name'>Model Name</Label>
                <TextField.Root
                    id='model_name'
                    {...register('model_name')}
                    placeholder={modelProvider === 'OpenAI' ? 'gpt-4o' : 'llama3-8b'}
                    aria-invalid={errors.model_name ? 'true' : 'false'}
                />
                <HelperText>
                    {modelProvider === 'OpenAI' ? 
                        'For OpenAI, use model names like "gpt-4o", "gpt-4-turbo", or "gpt-3.5-turbo".' : 
                        'For local models, use the name of the model as it appears in your local provider.'}
                </HelperText>
                {errors.model_name && <ErrorText>{errors.model_name?.message}</ErrorText>}
            </Stack>
            
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
            <Heading as='h5' size='2' className='not-cal' weight='medium'>RAG (Retrieval-Augmented Generation)</Heading>
            
            {modelProvider !== 'OpenAI' && (
                <Stack maxWidth={'560px'}>
                    <Text as="label" size="2">
                        <HStack align='center'>
                            <Controller
                                control={control}
                                name='enable_local_rag'
                                render={({ field }) => (
                                    <Checkbox
                                        checked={field.value ? true : false}
                                        onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                    />
                                )} />
                            <span>Enable Local RAG</span>
                            <Tooltip content='Enable local Retrieval-Augmented Generation'>
                                <span className='text-gray-11 -mb-1'>
                                    <BiInfoCircle size={16} />
                                </span>
                            </Tooltip>
                        </HStack>
                    </Text>
                    <HelperText>
                        Enable this to use local RAG with your selected model provider. This allows the bot to retrieve 
                        information from documents stored in a vector database.
                    </HelperText>
                </Stack>
            )}
            
            {modelProvider !== 'OpenAI' && enableLocalRAG && (
                <Stack maxWidth={'480px'}>
                    <Label htmlFor='local_rag_provider'>Local RAG Provider</Label>
                    <Controller
                        control={control}
                        name='local_rag_provider'
                        render={({ field }) => (
                            <Select.Root
                                value={field.value || ''}
                                onValueChange={field.onChange}
                            >
                                <Select.Trigger id='local_rag_provider' />
                                <Select.Content>
                                    <Select.Item value="Chroma">ChromaDB</Select.Item>
                                    <Select.Item value="FAISS">FAISS</Select.Item>
                                    <Select.Item value="Weaviate">Weaviate</Select.Item>
                                </Select.Content>
                            </Select.Root>
                        )}
                    />
                    <HelperText>
                        Select the vector database provider for local RAG. ChromaDB is recommended for most use cases.
                    </HelperText>
                </Stack>
            )}
            
            {modelProvider === 'OpenAI' && (
                <Stack maxWidth={'480px'}>
                    <Label htmlFor='vector_store_ids'>OpenAI Vector Store IDs</Label>
                    <TextField.Root
                        id='vector_store_ids'
                        {...register('vector_store_ids')}
                        placeholder="vs-abc123,vs-def456"
                        aria-invalid={errors.vector_store_ids ? 'true' : 'false'}
                    />
                    <HelperText>
                        Comma-separated list of OpenAI vector store IDs for RAG. Leave empty if not using OpenAI RAG.
                    </HelperText>
                    {errors.vector_store_ids && <ErrorText>{errors.vector_store_ids?.message}</ErrorText>}
                </Stack>
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

export default AIFeaturesBotForm