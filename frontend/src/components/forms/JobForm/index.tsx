import { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useToast } from '@/components/ui/toast';
import { api, handleApiError } from '@/lib/api';
import type { AgentSchemaResult, FormFieldSchema } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { LLMSelector } from '@/components/LLMSelector';

// Import scheduling components
import ScheduleToggle from './ScheduleToggle';

// Import extracted components
import { ErrorSummary } from './ErrorSummary';
import { SchemaLoadingProgress } from './SchemaLoadingProgress';
import { ValidationErrorDisplay } from './ValidationErrorDisplay';
import { FormField } from './FormField';

// Import validation utilities
import { createZodSchema, validateFieldValue } from './FormValidation';

// Import types
import type { 
  DynamicJobFormProps, 
  LoadingState, 
  FormErrorState
} from './types';

export function JobForm({ agentId, onJobCreated, editMode }: DynamicJobFormProps) {
  // Execution mode state - set to 'schedule' if editing a schedule
  const [executionMode, setExecutionMode] = useState<'now' | 'schedule'>(editMode ? 'schedule' : 'now');

  // State management
  const [agentSchema, setAgentSchema] = useState<AgentSchemaResult | null>(null);
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

  // Schedule-specific state
  const [cronExpression, setCronExpression] = useState<string>(
    editMode?.initialData?.cronExpression as string || '0 9 * * *'
  );
  const [scheduleEnabled, setScheduleEnabled] = useState<boolean>(
    editMode?.initialData?.scheduleEnabled as boolean ?? true
  );
  const [cronError, setCronError] = useState<string>('');

  // Form setup
  const form = useForm<Record<string, unknown>>({
    mode: 'onChange',
    resolver: formSchema ? zodResolver(createZodSchema(formSchema, requiredFields)) : undefined,
    defaultValues: {
      title: editMode?.initialData?.title || '',
      llm_provider: 'google',
      ...(editMode?.initialData || {})
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
      
      // Fields handled by LLMSelector - exclude from dynamic form
      const excludedFields = ['provider', 'model'];
      
      // Process each model schema
      Object.entries(response.schemas).forEach(([_modelName, modelSchema]) => {
        if (modelSchema.properties) {
          Object.entries(modelSchema.properties).forEach(([fieldName, fieldSchema]) => {
            // Skip fields handled by LLMSelector
            if (excludedFields.includes(fieldName)) {
              return;
            }
            
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
          
          // Add required fields from this model (excluding LLMSelector fields)
          if (modelSchema.required) {
            const filteredRequired = modelSchema.required.filter(field => !excludedFields.includes(field));
            allRequiredFields.push(...filteredRequired);
          }
        }
      });
      
      setFormSchema(convertedSchemas);
      setRequiredFields([...new Set(allRequiredFields)]); // Remove duplicates
      
      // Set default values from schema
      const defaults: Record<string, unknown> = { 
        title: editMode?.initialData?.title || '', 
        llm_provider: selectedProvider,
        ...(editMode?.initialData || {})
      };
      Object.entries(convertedSchemas).forEach(([key, fieldSchema]) => {
        if (fieldSchema.default !== undefined && !editMode?.initialData?.[key]) {
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
  }, [agentId, selectedProvider, reset, editMode]);

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

    // Validate schedule-specific fields if in schedule mode
    if (executionMode === 'schedule') {
      if (!cronExpression.trim()) {
        newErrorState.fieldErrors['cronExpression'] = {
          field: 'cronExpression',
          message: 'Cron expression is required',
          type: 'required',
          severity: 'error'
        };
        newErrorState.hasErrors = true;
      }
    }

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

  // Handle form submission for run now
  const onSubmit = async (data: Record<string, unknown>) => {
    setIsSubmitting(true);
    
    try {
      // Final validation
      if (!validateForm()) {
        toast.error('Please fix the errors in the form');
        return;
      }

      if (executionMode === 'schedule') {
        // Handle schedule creation
        await handleScheduleSubmit(data);
      } else {
        // Handle immediate job creation
        await handleJobSubmit(data);
      }

    } catch (error) {
      console.error('Form submission failed:', error);
      const errorMessage = handleApiError(error);
      toast.error(`Failed to ${executionMode === 'schedule' ? 'create schedule' : 'create job'}: ${errorMessage}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle immediate job submission
  const handleJobSubmit = async (data: Record<string, unknown>) => {
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
    
    if (response.job_id) {
      toast.success('Job created successfully');
      onJobCreated(response.job_id);
    } else {
      throw new Error('Invalid response from server');
    }
  };

  // Handle schedule submission
  const handleScheduleSubmit = async (data: Record<string, unknown>) => {
    // Prepare job data
    const { title, llm_provider, ...agentJobData } = data;
    
    // Get user's timezone
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    
    const scheduleData = {
      title: title,
      agent_name: agentId,
      cron_expression: cronExpression,
      enabled: scheduleEnabled,
      timezone: userTimezone, // Add user timezone
      agent_config_data: {
        name: agentId,
        description: title,
        profile: 'balanced',
        performance_mode: 'balanced',
        enabled: true,
        execution: {
          timeout_seconds: 300,
          max_retries: 3,
          enable_caching: true,
          priority: 5
        },
        model: {
          temperature: 0.7,
          max_tokens: 2000
        },
        logging: {
          log_level: 'INFO',
          enable_performance_logging: true
        },
        security: {
          enable_input_validation: true,
          enable_output_sanitization: true
        },
        job_data: {
          ...agentJobData,
          provider: selectedProvider,
          model: selectedModel || undefined
        },
        custom_settings: {}
      }
    };
    
    let response;
    if (editMode) {
      // Update existing schedule
      response = await api.schedules.update(editMode.scheduleId, scheduleData);
    } else {
      // Create new schedule
      response = await api.schedules.create(scheduleData);
    }
    
    if (response.success || response) {
      toast.success(`Schedule ${editMode ? 'updated' : 'created'} successfully`);
      onJobCreated(editMode ? editMode.scheduleId : response.result?.id || response.id);
    } else {
      throw new Error(response.message || `Failed to ${editMode ? 'update' : 'create'} schedule`);
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

  // Handle cron expression change
  const handleCronChange = (newCronExpression: string) => {
    setCronExpression(newCronExpression);
    setCronError('');
    
    // Clear cron-related errors
    if (formErrorState.fieldErrors['cronExpression']) {
      const { cronExpression: removed, ...remainingErrors } = formErrorState.fieldErrors;
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
          <CardTitle>{editMode ? 'Edit Schedule' : 'Create New Job'}</CardTitle>
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
                    disabled={isSubmitting}
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

            {/* Execution Mode Toggle */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Execution Mode</label>
              <ScheduleToggle
                mode={executionMode}
                onModeChange={setExecutionMode}
                disabled={isSubmitting}
              />
            </div>

            {/* Schedule-specific fields - shown only when schedule mode is selected */}
            {executionMode === 'schedule' && (
              <div className="space-y-4">
                {/* Cron Expression */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Schedule Pattern *</label>
                  <input
                    type="text"
                    value={cronExpression}
                    onChange={(e) => {
                      setCronExpression(e.target.value);
                      handleCronChange(e.target.value);
                    }}
                    className="w-full px-3 py-2 border rounded-md font-mono text-sm"
                    placeholder="0 9 * * * (minute hour day month weekday)"
                    disabled={isSubmitting}
                  />
                  {formErrorState.fieldErrors['cronExpression'] && (
                    <ValidationErrorDisplay 
                      error={{
                        field: 'cronExpression',
                        message: formErrorState.fieldErrors['cronExpression'].message,
                        type: formErrorState.fieldErrors['cronExpression'].type,
                        severity: formErrorState.fieldErrors['cronExpression'].severity
                      }}
                    />
                  )}
                  {cronError && (
                    <p className="text-sm text-red-600">{cronError}</p>
                  )}
                  <div className="text-xs text-gray-500">
                    <p>Examples: "0 9 * * *" (daily at 9 AM), "0 */6 * * *" (every 6 hours), "0 0 * * 1" (weekly on Monday)</p>
                  </div>
                </div>

                {/* Schedule Enabled */}
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="scheduleEnabled"
                      checked={scheduleEnabled}
                      onChange={(e) => setScheduleEnabled(e.target.checked)}
                      disabled={isSubmitting}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="scheduleEnabled" className="text-sm font-medium">
                      Enable schedule immediately
                    </label>
                  </div>
                </div>
              </div>
            )}

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
                    {editMode ? (executionMode === 'schedule' ? 'Updating Schedule...' : 'Updating...') : (executionMode === 'schedule' ? 'Creating Schedule...' : 'Creating...')}
                  </>
                ) : (
                  editMode ? (executionMode === 'schedule' ? 'Update Schedule' : 'Update Job') : (executionMode === 'schedule' ? 'Create Schedule' : 'Run Now')
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
} 