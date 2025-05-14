import { ErrorText, HelperText, Label } from '@/components/common/Form'
import { Loader } from '@/components/common/Loader'
import PageContainer from '@/components/layout/Settings/PageContainer'
import SettingsContentContainer from '@/components/layout/Settings/SettingsContentContainer'
import SettingsPageHeader from '@/components/layout/Settings/SettingsPageHeader'
import useRavenSettings from '@/hooks/fetchers/useRavenSettings'
import { RavenSettings } from '@/types/Raven/RavenSettings'
import { hasRavenAdminRole, isSystemManager } from '@/utils/roles'
import { CheckCircledIcon, CrossCircledIcon, UpdateIcon } from '@radix-ui/react-icons'
import { Badge, Box, Button, Card, Checkbox, Dialog, Flex, Separator, Text, TextField } from '@radix-ui/themes'
import { useFrappeGetCall, useFrappePostCall, useFrappeUpdateDoc } from 'frappe-react-sdk'
import { useEffect, useState } from 'react'
import { Controller, FormProvider, useForm } from 'react-hook-form'
import { toast } from 'sonner'

// Define types for the test results
interface LLMTestStatus {
    status: 'not_tested' | 'success' | 'error';
    message: string;
}

interface LLMTestResults {
    openai?: LLMTestStatus;
    local_llm?: LLMTestStatus;
    message?: string;
}

const LLMSettings = () => {
    const isRavenAdmin = hasRavenAdminRole() || isSystemManager()
    const { ravenSettings, mutate } = useRavenSettings()
    const [testResults, setTestResults] = useState<LLMTestResults | null>(null)
    const [isTesting, setIsTesting] = useState(false)
    const [showTestResults, setShowTestResults] = useState(false)
    
    const methods = useForm<RavenSettings>({
        disabled: !isRavenAdmin
    })
    
    // Hook to call the test API
    const { call: testLLMConfiguration } = useFrappePostCall('raven.api.ai_features.test_llm_configuration')

    const { handleSubmit, control, watch, reset, register, formState: { errors } } = methods

    useEffect(() => {
        if (ravenSettings) {
            // Set default provider if not set
            if (ravenSettings.enable_local_llm && !ravenSettings.local_llm_provider) {
                ravenSettings.local_llm_provider = 'LM Studio';
            }
            
            // Reset form with settings
            reset(ravenSettings);
        }
    }, [ravenSettings])

    const { updateDoc, loading: updatingDoc } = useFrappeUpdateDoc<RavenSettings>()

    const onSubmit = (data: RavenSettings) => {
        toast.promise(updateDoc('Raven Settings', null, {
            ...(ravenSettings ?? {}),
            ...data
        }).then(res => {
            mutate(res, {
                revalidate: false
            })
        }), {
            loading: 'Updating...',
            success: () => {
                return `Settings updated`;
            },
            error: 'There was an error.',
        })
    }

    useEffect(() => {

        const down = (e: KeyboardEvent) => {
            if (e.key === 's' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                methods.handleSubmit(onSubmit)()
            }
        }

        document.addEventListener('keydown', down)
        return () => document.removeEventListener('keydown', down)
    }, [])

    const isAIEnabled = watch('enable_ai_integration')
    const isLocalLLMEnabled = watch('enable_local_llm')

    const { data: openaiVersion } = useFrappeGetCall<{ message: string }>('raven.api.ai_features.get_open_ai_version')
    
    // Function to test LLM configurations
    const handleTestConfiguration = async () => {
        // Get current form values
        const formData = methods.getValues();
        
        // Save form data first to ensure we test the latest config
        try {
            await updateDoc('Raven Settings', null, {
                ...(ravenSettings ?? {}),
                ...formData
            });
            
            setIsTesting(true);
            
            // Test the configuration
            try {
                const result = await testLLMConfiguration({});
                
                // Log the raw result to understand its structure
                console.log("Raw test result:", result);
                
                if (!result) {
                    setTestResults({ message: "No response received from server." });
                } else {
                    // Make sure we handle the result as an object with the expected structure
                    if (typeof result === 'object') {
                        // Convert the result message property if it's not in expected format
                        const processedResult: LLMTestResults = {
                            message: "Test completed. Results are shown below."
                        };
                        
                        // If result.message is present in the correct Frappe API response format
                        if (result.message && typeof result.message === 'object') {
                            // Frappe API sometimes wraps the response in a message property
                            // Check if this is the case here
                            if (result.message.openai && typeof result.message.openai === 'object') {
                                processedResult.openai = {
                                    status: result.message.openai.status as any || 'not_tested',
                                    message: result.message.openai.message || 'No details provided'
                                };
                            }
                            
                            if (result.message.local_llm && typeof result.message.local_llm === 'object') {
                                processedResult.local_llm = {
                                    status: result.message.local_llm.status as any || 'not_tested',
                                    message: result.message.local_llm.message || 'No details provided'
                                };
                            }
                        } else {
                            // Handle direct result structure
                            if (result.openai && typeof result.openai === 'object') {
                                processedResult.openai = {
                                    status: result.openai.status as any || 'not_tested',
                                    message: result.openai.message || 'No details provided'
                                };
                            }
                            
                            if (result.local_llm && typeof result.local_llm === 'object') {
                                processedResult.local_llm = {
                                    status: result.local_llm.status as any || 'not_tested',
                                    message: result.local_llm.message || 'No details provided'
                                };
                            }
                        }
                        
                        // Log processed result for debugging
                        console.log("Processed test result:", processedResult);
                        
                        setTestResults(processedResult);
                    } else {
                        // If result is not an object, create a fallback
                        setTestResults({ 
                            message: "Received invalid response format from server." 
                        });
                    }
                }
                
                // Show the results dialog
                setShowTestResults(true);
            } catch (error: any) {
                setTestResults({ 
                    message: `Failed to test LLM configuration: ${error.message || "Unknown error"}` 
                });
                setShowTestResults(true);
            }
        } catch (error: any) {
            toast.error(`Failed to save settings before testing: ${error.message || "Unknown error"}`);
        } finally {
            setIsTesting(false);
        }
    }

    return (
        <PageContainer>
            <FormProvider {...methods}>
                <form onSubmit={handleSubmit(onSubmit)}>
                    <SettingsContentContainer>
                        <SettingsPageHeader
                            title='LLM Settings'
                            description='Configure LLM settings including OpenAI and Local LLM options.'
                            actions={
                                <Flex gap="2">
                                    <Button 
                                        onClick={handleTestConfiguration} 
                                        disabled={updatingDoc || isTesting || !isRavenAdmin}
                                        variant="soft"
                                    >
                                        {isTesting ? <Loader className="text-gray-900" /> : <UpdateIcon />}
                                        {isTesting ? "Testing" : "Test Connection"}
                                    </Button>
                                    <Button type='submit' disabled={updatingDoc || !isRavenAdmin}>
                                        {updatingDoc && <Loader className="text-white" />}
                                        {updatingDoc ? "Saving" : "Save"}
                                    </Button>
                                </Flex>
                            }
                        />

                        <Flex direction={'column'} gap='2'>
                            <Text as="label" size="2">
                                <Flex gap="2">
                                    <Controller
                                        control={control}
                                        defaultValue={ravenSettings?.enable_ai_integration}
                                        name='enable_ai_integration'
                                        render={({ field }) => (
                                            <Checkbox
                                                checked={field.value ? true : false}
                                                name={field.name}
                                                disabled={field.disabled}
                                                onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                            />
                                        )} />

                                    Enable AI Integration
                                </Flex>
                            </Text>
                        </Flex>
                        <Separator size='4' />
                        
                        {isAIEnabled ?
                            <>                                
                                {/* OpenAI Services Toggle */}
                                <Flex direction={'column'} gap='2'>
                                    <Text as="label" size="2">
                                        <Flex gap="2">
                                            <Controller
                                                control={control}
                                                defaultValue={ravenSettings?.enable_openai_services}
                                                name='enable_openai_services'
                                                render={({ field }) => (
                                                    <Checkbox
                                                        checked={field.value ? true : false}
                                                        name={field.name}
                                                        disabled={field.disabled}
                                                        onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                                    />
                                                )} />
                                            Enable OpenAI Services
                                        </Flex>
                                    </Text>
                                </Flex>
                                
                                {/* OpenAI Specific Fields */}
                                {watch('enable_openai_services') && (
                                    <Box>
                                        <Label htmlFor='openai_organisation_id' isRequired>OpenAI Organization ID</Label>
                                        <TextField.Root
                                            autoFocus
                                            maxLength={140}
                                            className={'w-48 sm:w-96'}
                                            id='openai_organisation_id'
                                            autoComplete='off'
                                            required
                                            placeholder='org-************************'
                                            {...register('openai_organisation_id', {
                                                required: watch('enable_openai_services') ? "Please add your OpenAI Organization ID" : false,
                                                maxLength: {
                                                    value: 140,
                                                    message: "ID cannot be more than 140 characters."
                                                }
                                            })}
                                            aria-invalid={errors.openai_organisation_id ? 'true' : 'false'}
                                        />
                                        {errors?.openai_organisation_id && <ErrorText>{errors.openai_organisation_id?.message}</ErrorText>}
                                    </Box>
                                )}
                            </>
                            : null
                        }

                        {isAIEnabled && watch('enable_openai_services') ?
                            <Box>
                                <Label htmlFor='openai_api_key' isRequired>OpenAI API Key</Label>
                                <TextField.Root
                                    className={'w-48 sm:w-96'}
                                    id='openai_api_key'
                                    required
                                    type='password'
                                    autoComplete='off'
                                    placeholder='••••••••••••••••••••••••••••••••'
                                    {...register('openai_api_key', {
                                        required: watch('enable_openai_services') ? "Please add your OpenAI API Key" : false,
                                    })}
                                    aria-invalid={errors.openai_api_key ? 'true' : 'false'}
                                />
                                {errors?.openai_api_key && <ErrorText>{errors.openai_api_key?.message}</ErrorText>}
                            </Box>
                            : null
                        }

                        {isAIEnabled && watch('enable_openai_services') ?
                            <Box>
                                <Label htmlFor='openai_project_id'>OpenAI Project ID</Label>
                                <TextField.Root
                                    maxLength={140}
                                    className={'w-48 sm:w-96'}
                                    id='openai_project_id'
                                    autoComplete='off'
                                    placeholder='proj_************************'
                                    {...register('openai_project_id', {
                                        maxLength: {
                                            value: 140,
                                            message: "ID cannot be more than 140 characters."
                                        }
                                    })}
                                    aria-invalid={errors.openai_project_id ? 'true' : 'false'}
                                />
                                {errors?.openai_project_id && <ErrorText>{errors.openai_project_id?.message}</ErrorText>}
                                <HelperText>
                                    If not set, the integration will use the default project.
                                </HelperText>
                            </Box>
                            : null
                        }

                        {isAIEnabled && watch('enable_openai_services') ?
                            <Box>
                                {openaiVersion && <Text color='gray' size='2'>OpenAI Python SDK Version: {openaiVersion.message}</Text>}
                            </Box>
                            : null
                        }
                        

                        {isAIEnabled ? <Separator size='4' /> : null}

                        {/* Local LLM Configuration Section */}
                        {isAIEnabled ? (
                            <Flex direction={'column'} gap='2'>
                            <Text as="label" size="2">
                                <Flex gap="2">
                                    <Controller
                                        control={control}
                                        defaultValue={ravenSettings?.enable_local_llm}
                                        name='enable_local_llm'
                                        render={({ field }) => (
                                            <Checkbox
                                                checked={field.value ? true : false}
                                                name={field.name}
                                                disabled={field.disabled}
                                                onCheckedChange={(v) => field.onChange(v ? 1 : 0)}
                                            />
                                        )} />
                                    Enable Local LLM Integration
                                </Flex>
                            </Text>
                        </Flex>
                        ) : null}
                        
                        {isAIEnabled && isLocalLLMEnabled ?
                            <Box>
                                <Label htmlFor='local_llm_provider'>Local LLM Provider</Label>
                                <Flex direction="column" gap="1">
                                    <Controller
                                        control={control}
                                        name='local_llm_provider'
                                        defaultValue={ravenSettings?.local_llm_provider || 'LM Studio'}
                                        render={({ field }) => (
                                            <select
                                                className='w-48 sm:w-96 h-8 px-2 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
                                                id='local_llm_provider'
                                                value={field.value}
                                                onChange={(e) => {
                                                    field.onChange(e.target.value);
                                                    // Set default URL based on selected provider
                                                    let defaultUrl = '';
                                                    switch (e.target.value) {
                                                        case 'LM Studio':
                                                            defaultUrl = 'http://localhost:1234/v1';
                                                            break;
                                                        case 'Ollama':
                                                            defaultUrl = 'http://localhost:11434/v1';
                                                            break;
                                                        case 'LocalAI':
                                                            defaultUrl = 'http://localhost:8080/v1';
                                                            break;
                                                    }
                                                    // Update the URL field with the default for the selected provider
                                                    if (!methods.getValues('local_llm_api_url')) {
                                                        methods.setValue('local_llm_api_url', defaultUrl);
                                                    }
                                                }}
                                            >
                                                <option value="LM Studio">LM Studio</option>
                                                <option value="Ollama">Ollama</option>
                                                <option value="LocalAI">LocalAI</option>
                                            </select>
                                        )}
                                    />
                                    <HelperText>
                                        Select your local LLM provider
                                    </HelperText>
                                </Flex>
                            </Box>
                            : null
                        }

                        {isAIEnabled && isLocalLLMEnabled ?
                            <Box>
                                <Label htmlFor='local_llm_api_url'>Local LLM API URL</Label>
                                <TextField.Root
                                    className={'w-48 sm:w-96'}
                                    id='local_llm_api_url'
                                    type='url'
                                    autoComplete='off'
                                    placeholder={(() => {
                                        const provider = methods.getValues('local_llm_provider') || 'LM Studio';
                                        switch (provider) {
                                            case 'LM Studio': return 'http://localhost:1234/v1';
                                            case 'Ollama': return 'http://localhost:11434/v1';
                                            case 'LocalAI': return 'http://localhost:8080/v1';
                                            default: return 'http://localhost:1234/v1';
                                        }
                                    })()}
                                    {...register('local_llm_api_url')}
                                    aria-invalid={errors.local_llm_api_url ? 'true' : 'false'}
                                />
                                {errors?.local_llm_api_url && <ErrorText>{errors.local_llm_api_url?.message}</ErrorText>}
                                <HelperText>
                                    {(() => {
                                        const provider = methods.getValues('local_llm_provider') || 'LM Studio';
                                        switch (provider) {
                                            case 'LM Studio': return 'URL for the local LM Studio API (e.g., http://localhost:1234/v1)';
                                            case 'Ollama': return 'URL for the local Ollama API (e.g., http://localhost:11434/v1)';
                                            case 'LocalAI': return 'URL for the local LocalAI API (e.g., http://localhost:8080/v1)';
                                            default: return 'URL for the selected local LLM API';
                                        }
                                    })()}
                                </HelperText>
                            </Box>
                            : null
                        }
                        
                        
                        

                        
                    </SettingsContentContainer>
                </form>
            </FormProvider>
            
            {/* Test Results Dialog */}
            <Dialog.Root open={showTestResults} onOpenChange={setShowTestResults}>
                <Dialog.Content size="3">
                    <Dialog.Title>LLM Configuration Test Results</Dialog.Title>
                    <Dialog.Description>
                        Results of testing the LLM configuration settings
                    </Dialog.Description>
                    
                    {testResults?.message && (
                        <Box mb="4">
                            <Text>{testResults.message}</Text>
                        </Box>
                    )}
                    
                    {/* Add a debug section in development environment */}
                    {process.env.NODE_ENV !== 'production' && (
                        <Box mb="4" py="2" px="3" style={{backgroundColor: '#f5f5f5', borderRadius: '6px'}}>
                            <Text size="1" weight="bold">Debug Information:</Text>
                            <Text size="1" style={{wordBreak: 'break-all', fontFamily: 'monospace'}}>
                                Test Results Object: {JSON.stringify(testResults)}
                            </Text>
                        </Box>
                    )}
                    
                    {/* Default OpenAI result card when needed */}
                    {(testResults?.openai && typeof testResults.openai === 'object') ? (
                        <Card size="1" className="mt-2 mb-2">
                            <Flex direction="column" gap="2">
                                <Flex align="center" gap="2">
                                    {testResults.openai.status === 'success' ? (
                                        <CheckCircledIcon className="text-green-500" />
                                    ) : testResults.openai.status === 'error' ? (
                                        <CrossCircledIcon className="text-red-500" />
                                    ) : null}
                                    <Text size="2" weight="bold">OpenAI</Text>
                                    <Badge 
                                        color={testResults.openai.status === 'success' ? 'green' : 
                                            testResults.openai.status === 'error' ? 'red' : 'gray'}
                                    >
                                        {testResults.openai.status === 'success' ? 'Connected' : 
                                        testResults.openai.status === 'error' ? 'Error' : 'Not Tested'}
                                    </Badge>
                                </Flex>
                                <Text size="2">{testResults.openai.message || ''}</Text>
                            </Flex>
                        </Card>
                    ) : watch('enable_ai_integration') && watch('enable_openai_services') ? (
                        <Card size="1" className="mt-2 mb-2">
                            <Flex direction="column" gap="2">
                                <Flex align="center" gap="2">
                                    <CrossCircledIcon className="text-red-500" />
                                    <Text size="2" weight="bold">OpenAI</Text>
                                    <Badge color="red">Not Available</Badge>
                                </Flex>
                                <Text size="2">Response data for OpenAI was not in the expected format.</Text>
                            </Flex>
                        </Card>
                    ) : null}
                    
                    {/* Default Local LLM result card when needed */}
                    {(testResults?.local_llm && typeof testResults.local_llm === 'object') ? (
                        <Card size="1" className="mt-2 mb-2">
                            <Flex direction="column" gap="2">
                                <Flex align="center" gap="2">
                                    {testResults.local_llm.status === 'success' ? (
                                        <CheckCircledIcon className="text-green-500" />
                                    ) : testResults.local_llm.status === 'error' ? (
                                        <CrossCircledIcon className="text-red-500" />
                                    ) : null}
                                    <Text size="2" weight="bold">{methods.getValues('local_llm_provider') || 'Local LLM'}</Text>
                                    <Badge 
                                        color={testResults.local_llm.status === 'success' ? 'green' : 
                                            testResults.local_llm.status === 'error' ? 'red' : 'gray'}
                                    >
                                        {testResults.local_llm.status === 'success' ? 'Connected' : 
                                        testResults.local_llm.status === 'error' ? 'Error' : 'Not Tested'}
                                    </Badge>
                                </Flex>
                                <Text size="2">{testResults.local_llm.message || ''}</Text>
                            </Flex>
                        </Card>
                    ) : watch('enable_local_llm') ? (
                        <Card size="1" className="mt-2 mb-2">
                            <Flex direction="column" gap="2">
                                <Flex align="center" gap="2">
                                    <CrossCircledIcon className="text-red-500" />
                                    <Text size="2" weight="bold">{methods.getValues('local_llm_provider') || 'Local LLM'}</Text>
                                    <Badge color="red">Not Available</Badge>
                                </Flex>
                                <Text size="2">Response data for Local LLM was not in the expected format.</Text>
                            </Flex>
                        </Card>
                    ) : null}
                    
                    <Flex gap="3" mt="4" justify="end">
                        <Dialog.Close>
                            <Button variant="soft" color="gray">Close</Button>
                        </Dialog.Close>
                    </Flex>
                </Dialog.Content>
            </Dialog.Root>
        </PageContainer>
    )
}

export const Component = LLMSettings