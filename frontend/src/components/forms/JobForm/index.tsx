import { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useToast } from '@/components/ui/toast';
import { api, handleApiError } from '@/lib/api';
import type { AgentSchemaResponse, FormFieldSchema } from '@/lib/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { LLMSelector } from '@/components/LLMSelector';

// Import extracted components
import { ErrorSummary } from './ErrorSummary';
import { SchemaLoadingProgress } from './SchemaLoadingProgress';
import { ValidationErrorDisplay } from './ValidationErrorDisplay';
import { FormField } from './FormField';

// Import validation utilities
import { createZodSchema, validateFieldValue, parseApiError } from './FormValidation';

// Import types
import type { 
  DynamicJobFormProps, 
  LoadingState, 
  FormErrorState
} from './types';

export function JobForm({ agentId, onJobCreated }: DynamicJobFormProps) {
  // State management
  const [agentSchema, setAgentSchema] = useState<AgentSchemaResponse | null>(null);
  const [formSchema, setFormSchema] = useState<Record<string, FormFieldSchema> | null>(null);
  const [requiredFields, setRequiredFields] = useState<string[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    stage: 'fetching',
    progress: 0,
    message: 'Initializing...',
    hasError: false,
    canRetry: true
  });
  
  const [formErrorState, setFormErrorState] = useState<FormErrorState>({
    hasErrors: false,
    fieldErrors: {},
    globalErrors: [],
    warnings: [],
    apiErrors: []
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<string>('google');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const toast = useToast();

  // Form setup
  const form = useForm<Record<string, unknown>>({
    mode: 'onChange',
    resolver: formSchema ? zodResolver(createZodSchema(formSchema, requiredFields)) : undefined,
    defaultValues: {
      title: '',
      llm_provider: 'google'
    }
  });

  const { handleSubmit, control, formState: { errors }, setValue, watch, reset } = form;

  // Load agent schema
  const loadAgentSchema = useCallback(async () => {
    if (!agentId) return;

    setLoadingState({
      isLoading: true,
      stage: 'fetching',
      progress: 10,
      message: 'Fetching agent information...',
      hasError: false,
      canRetry: true
    });

    try {
      setLoadingState(prev => ({ ...prev, stage: 'parsing', progress: 40, message: 'Loading schema...' }));
      
      const response = await api.agents.getSchema(agentId);
      
      setLoadingState(prev => ({ ...prev, stage: 'validating', progress: 80, message: 'Validating schema...' }));
      
      if (!response.schemas) {
        throw new Error('Invalid schema response');
      }

      setAgentSchema(response);
      
      // Convert agent schemas to form field schemas
      const convertedSchemas: Record<string, FormFieldSchema> = {};
      const allRequiredFields: string[] = [];
      
      // Process each model schema
      Object.entries(response.schemas).forEach(([_modelName, modelSchema]) => {
        if (modelSchema.properties) {
          Object.entries(modelSchema.properties).forEach(([fieldName, fieldSchema]) => {
            // Convert AgentSchema property to FormFieldSchema
            const formFieldSchema: FormFieldSchema = {
              type: fieldSchema.type || 'string',
              title: fieldSchema.title || fieldName,
              description: fieldSchema.description,
              default: fieldSchema.default,
              enum: fieldSchema.enum,
              format: fieldSchema.format,
              minLength: fieldSchema.minLength,
              maxLength: fieldSchema.maxLength,
              minimum: fieldSchema.minimum,
              maximum: fieldSchema.maximum,
              pattern: fieldSchema.pattern,
              form_field_type: fieldSchema.form_field_type, // Keep for backward compatibility, but FormField will infer if not present
              anyOf: fieldSchema.anyOf // Transfer anyOf for Optional field handling
            };
            
            convertedSchemas[fieldName] = formFieldSchema;
          });
          
          // Add required fields from this model
          if (modelSchema.required) {
            allRequiredFields.push(...modelSchema.required);
          }
        }
      });
      
      setFormSchema(convertedSchemas);
      setRequiredFields([...new Set(allRequiredFields)]); // Remove duplicates
      
      // Set default values from schema
      const defaults: Record<string, unknown> = { title: '', llm_provider: selectedProvider };
      Object.entries(convertedSchemas).forEach(([key, fieldSchema]) => {
        if (fieldSchema.default !== undefined) {
          defaults[key] = fieldSchema.default;
        }
      });
      
      reset(defaults);
      
      setLoadingState({
        isLoading: false,
        stage: 'ready',
        progress: 100,
        message: 'Schema loaded successfully',
        hasError: false,
        canRetry: false
      });

    } catch (error) {
      console.error('Failed to load agent schema:', error);
      setLoadingState({
        isLoading: false,
        stage: 'fetching',
        progress: 0,
        message: error instanceof Error ? error.message : 'Failed to load agent schema',
        hasError: true,
        canRetry: true
      });
    }
  }, [agentId, selectedProvider, reset]);

  // Load schema on component mount
  useEffect(() => {
    loadAgentSchema();
  }, [loadAgentSchema]);

  // Form validation
  const validateForm = () => {
    const formData = watch();
    const newErrorState: FormErrorState = {
      hasErrors: false,
      fieldErrors: {},
      globalErrors: [],
      warnings: [],
      apiErrors: []
    };

    if (!formSchema) {
      newErrorState.globalErrors.push('Agent schema not loaded');
      newErrorState.hasErrors = true;
      setFormErrorState(newErrorState);
      return false;
    }

    // Validate each field
    Object.entries(formSchema).forEach(([fieldName, fieldSchema]) => {
      const value = formData[fieldName];
      
      const error = validateFieldValue(fieldName, value, fieldSchema, requiredFields);
      if (error) {
        newErrorState.fieldErrors[fieldName] = error;
        newErrorState.hasErrors = true;
      }
    });

    setFormErrorState(newErrorState);
    return !newErrorState.hasErrors;
  };

  // Focus on field with error
  const focusOnField = (fieldName: string) => {
    const element = document.querySelector(`[name="${fieldName}"]`) as HTMLElement;
    if (element) {
      element.focus();
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Handle form submission
  const onSubmit = async (data: Record<string, unknown>) => {
    setIsSubmitting(true);
    
    try {
      // Final validation
      if (!validateForm()) {
        toast.error('Please fix the errors in the form');
        return;
      }

      // Prepare job data
      const jobData = { ...data };
      
      // Remove title from job data (it's used for job metadata)
      const { title, llm_provider, ...agentJobData } = jobData;
      
      const jobRequest = {
        agent_identifier: agentId,
        data: { 
          ...agentJobData, 
          provider: selectedProvider,
          model: selectedModel || undefined
        },
        title: String(title || `${agentId} Job`),
        priority: 5
      };

      const response = await api.jobs.create(jobRequest);
      
      if (response.success && response.job_id) {
        onJobCreated(response.job_id);
      } else {
        throw new Error('Invalid response from server');
      }

    } catch (error) {
      console.error('Job creation failed:', error);
      
      // Parse API errors
      const errorMessage = handleApiError(error);
      const apiErrors = parseApiError(errorMessage);
      
      setFormErrorState(prev => ({
        ...prev,
        hasErrors: true,
        apiErrors,
        globalErrors: [...prev.globalErrors, 'Failed to create job']
      }));
      
      toast.error('Failed to create job');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Retry loading schema
  const handleRetry = () => {
    loadAgentSchema();
  };

  // Handle field changes
  const handleFieldChange = (fieldName: string, value: unknown) => {
    setValue(fieldName, value);
    
    // Clear field-specific errors
    if (formErrorState.fieldErrors[fieldName]) {
      const { [fieldName]: removed, ...remainingErrors } = formErrorState.fieldErrors;
      setFormErrorState(prev => ({
        ...prev,
        fieldErrors: remainingErrors
      }));
    }
  };

  // Show loading state
  if (loadingState.isLoading || loadingState.hasError) {
    return (
      <div className="space-y-4">
        <SchemaLoadingProgress 
          loadingState={loadingState}
          onRetry={handleRetry}
          agentName={agentId}
        />
      </div>
    );
  }

  if (!agentSchema || !formSchema) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">
            No schema available for this agent
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Summary */}
      <ErrorSummary errorState={formErrorState} onFieldFocus={focusOnField} />

      {/* Main Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Job</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Job Title */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Job Title *</label>
              <Controller
                name="title"
                control={control}
                render={({ field }) => (
                  <input
                    {...field}
                    value={String(field.value || '')}
                    type="text"
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Enter a descriptive title for this job"
                  />
                )}
              />
              {errors.title && (
                <ValidationErrorDisplay 
                  error={{
                    field: 'title',
                    message: String(errors.title.message),
                    type: 'required',
                    severity: 'error'
                  }}
                />
              )}
            </div>

            {/* LLM Provider Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">AI Provider</label>
              <LLMSelector
                selectedProvider={selectedProvider}
                selectedModel={selectedModel}
                onProviderChange={setSelectedProvider}
                onModelChange={setSelectedModel}
                disabled={isSubmitting}
              />
            </div>

            {/* Dynamic Form Fields */}
            <div className="space-y-4">
              {Object.entries(formSchema).map(([fieldName, fieldSchema]) => (
                <FormField
                  key={fieldName}
                  name={fieldName}
                  schema={fieldSchema}
                  control={control}
                  errors={errors}
                  disabled={isSubmitting}
                  isRequired={requiredFields.includes(fieldName)}
                  validationError={formErrorState.fieldErrors[fieldName]}
                  onFieldChange={handleFieldChange}
                />
              ))}
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-3">
              <Button
                type="submit"
                disabled={isSubmitting || formErrorState.hasErrors}
                className="min-w-32"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Job'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
} 