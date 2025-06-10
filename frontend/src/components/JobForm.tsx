import React, { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useToast } from '@/components/ui/toast';
import { responsiveForm } from '@/lib/responsive';
import { api, handleApiError } from '@/lib/api';
import type { AgentSchemaResponse, FormFieldSchema } from '@/lib/models';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, AlertCircle, CheckCircle, Info, RefreshCw, Wifi, WifiOff, Clock, Zap, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Control, FieldErrors } from 'react-hook-form';
import { LLMSelector } from '@/components/LLMSelector';

interface DynamicJobFormProps {
  agentId: string;
  onJobCreated: (jobId: string) => void;
}

// Enhanced loading states
interface LoadingState {
  isLoading: boolean;
  stage: 'fetching' | 'parsing' | 'validating' | 'ready';
  progress: number;
  message: string;
  hasError: boolean;
  canRetry: boolean;
}

// Enhanced error handling types
interface ValidationError {
  field: string;
  message: string;
  type: 'required' | 'format' | 'range' | 'constraint' | 'custom';
  severity: 'error' | 'warning';
  suggestion?: string;
}

interface FormErrorState {
  hasErrors: boolean;
  fieldErrors: Record<string, ValidationError>;
  globalErrors: string[];
  warnings: string[];
  apiErrors: ApiValidationError[];
}

interface ApiValidationError {
  field?: string;
  message: string;
  code?: string;
  details?: unknown;
}

// Error recovery suggestions
const getErrorSuggestion = (error: ValidationError, schema: FormFieldSchema): string => {
  switch (error.type) {
    case 'required':
      return `This field is required. Please provide a ${schema.title?.toLowerCase() || 'value'}.`;
    case 'format':
      if (schema.form_field_type === 'email') {
        return 'Please enter a valid email address (e.g., user@example.com).';
      }
      if (schema.form_field_type === 'url') {
        return 'Please enter a valid URL (e.g., https://example.com).';
      }
      return 'Please check the format of your input.';
    case 'range':
      if (schema.minimum !== undefined && schema.maximum !== undefined) {
        return `Value must be between ${schema.minimum} and ${schema.maximum}.`;
      }
      if (schema.minimum !== undefined) {
        return `Value must be at least ${schema.minimum}.`;
      }
      if (schema.maximum !== undefined) {
        return `Value must not exceed ${schema.maximum}.`;
      }
      return 'Value is outside the allowed range.';
    case 'constraint':
      if (schema.minLength !== undefined && schema.maxLength !== undefined) {
        return `Text must be between ${schema.minLength} and ${schema.maxLength} characters.`;
      }
      if (schema.minLength !== undefined) {
        return `Text must be at least ${schema.minLength} characters long.`;
      }
      if (schema.maxLength !== undefined) {
        return `Text must not exceed ${schema.maxLength} characters.`;
      }
      return 'Input does not meet the required constraints.';
    default:
      return 'Please correct this field and try again.';
  }
};

// Enhanced form validation with better error categorization
const validateFieldValue = (
  fieldName: string, 
  value: unknown, 
  schema: FormFieldSchema, 
  isRequired: boolean
): ValidationError | null => {
  // Check if required field is empty
  if (isRequired && (value === '' || value === null || value === undefined)) {
    return {
      field: fieldName,
      message: `${schema.title || fieldName} is required`,
      type: 'required',
      severity: 'error',
      suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'required', severity: 'error' }, schema)
    };
  }

  // Skip validation for empty optional fields
  if (!isRequired && (value === '' || value === null || value === undefined)) {
    return null;
  }

  // Type-specific validation
  switch (schema.form_field_type) {
    case 'email': {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(String(value))) {
        return {
          field: fieldName,
          message: 'Invalid email format',
          type: 'format',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'format', severity: 'error' }, schema)
        };
      }
      break;
    }

    case 'url':
      try {
        new URL(String(value));
      } catch {
        return {
          field: fieldName,
          message: 'Invalid URL format',
          type: 'format',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'format', severity: 'error' }, schema)
        };
      }
      break;

    case 'object': {
      // Validate JSON syntax for object fields
      if (value && typeof value === 'string' && value.trim() !== '') {
        try {
          const parsed = JSON.parse(value);
          // Ensure it's actually an object, not a primitive
          if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
            return {
              field: fieldName,
              message: 'Must be a valid JSON object (e.g., {"key": "value"})',
              type: 'format',
              severity: 'error',
              suggestion: 'Enter a valid JSON object with key-value pairs.'
            };
          }
        } catch {
          return {
            field: fieldName,
            message: 'Invalid JSON format',
            type: 'format',
            severity: 'error',
            suggestion: 'Check your JSON syntax. Example: {"key": "value", "another": "example"}'
          };
        }
      }
      break;
    }

    case 'number': {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return {
          field: fieldName,
          message: 'Must be a valid number',
          type: 'format',
          severity: 'error'
        };
      }
      if (schema.minimum !== undefined && numValue < schema.minimum) {
        return {
          field: fieldName,
          message: `Must be at least ${schema.minimum}`,
          type: 'range',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'range', severity: 'error' }, schema)
        };
      }
      if (schema.maximum !== undefined && numValue > schema.maximum) {
        return {
          field: fieldName,
          message: `Must not exceed ${schema.maximum}`,
          type: 'range',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'range', severity: 'error' }, schema)
        };
      }
      break;
    }

    case 'text':
    case 'textarea': {
      const strValue = String(value);
      if (schema.minLength !== undefined && strValue.length < schema.minLength) {
        return {
          field: fieldName,
          message: `Must be at least ${schema.minLength} characters`,
          type: 'constraint',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'constraint', severity: 'error' }, schema)
        };
      }
      if (schema.maxLength !== undefined && strValue.length > schema.maxLength) {
        return {
          field: fieldName,
          message: `Must not exceed ${schema.maxLength} characters`,
          type: 'constraint',
          severity: 'error',
          suggestion: getErrorSuggestion({ field: fieldName, message: '', type: 'constraint', severity: 'error' }, schema)
        };
      }
      if (schema.pattern) {
        const regex = new RegExp(schema.pattern);
        if (!regex.test(strValue)) {
          return {
            field: fieldName,
            message: 'Does not match required pattern',
            type: 'constraint',
            severity: 'error'
          };
        }
      }
      break;
    }
  }

  return null;
};

// Helper function to create Zod schema from JSON schema
const createZodSchema = (schema: Record<string, FormFieldSchema>, required: string[]) => {
  const shape: Record<string, z.ZodTypeAny> = {};
  
  // Always require title
  shape.title = z.string().min(1, 'Job title is required');
  
  for (const [fieldName, fieldSchema] of Object.entries(schema)) {
    let zodField: z.ZodTypeAny;
    
    switch (fieldSchema.form_field_type) {
      case 'number':
        zodField = z.number();
        if (fieldSchema.minimum !== undefined) {
          zodField = (zodField as z.ZodNumber).min(fieldSchema.minimum);
        }
        if (fieldSchema.maximum !== undefined) {
          zodField = (zodField as z.ZodNumber).max(fieldSchema.maximum);
        }
        break;
      
      case 'checkbox':
        zodField = z.boolean();
        break;
      
      case 'select':
        if (fieldSchema.enum) {
          zodField = z.enum(fieldSchema.enum as [string, ...string[]]);
        } else {
          zodField = z.string();
        }
        break;
      
      case 'email':
        zodField = z.string().email('Invalid email format');
        break;
      
      case 'url':
        zodField = z.string().url('Invalid URL format');
        break;
      
      default:
        zodField = z.string();
        if (fieldSchema.minLength) {
          zodField = (zodField as z.ZodString).min(fieldSchema.minLength);
        }
        if (fieldSchema.maxLength) {
          zodField = (zodField as z.ZodString).max(fieldSchema.maxLength);
        }
        if (fieldSchema.pattern) {
          zodField = (zodField as z.ZodString).regex(new RegExp(fieldSchema.pattern));
        }
        break;
    }
    
    // Make field optional if not in required array
    if (!required.includes(fieldName)) {
      zodField = zodField.optional();
    }
    
    shape[fieldName] = zodField;
  }
  
  return z.object(shape);
};

// Enhanced error display component
const ValidationErrorDisplay: React.FC<{
  error: ValidationError;
  className?: string;
}> = ({ error, className }) => {
  const getErrorIcon = () => {
    switch (error.severity) {
      case 'warning':
        return <AlertCircle className="h-3 w-3 text-yellow-500" />;
      default:
        return <AlertCircle className="h-3 w-3 text-red-500" />;
    }
  };

  const getErrorColor = () => {
    switch (error.severity) {
      case 'warning':
        return 'text-yellow-600';
      default:
        return 'text-red-500';
    }
  };

  return (
    <div className={cn("space-y-1", className)}>
      <div className={cn("text-sm flex items-center gap-1", getErrorColor())}>
        {getErrorIcon()}
        <span className="font-medium">{error.message}</span>
      </div>
      {error.suggestion && (
        <p className="text-xs text-muted-foreground pl-4">
          💡 {error.suggestion}
        </p>
      )}
    </div>
  );
};

// Error summary component for displaying multiple validation errors
const ErrorSummary: React.FC<{
  errorState: FormErrorState;
  onFieldFocus?: (fieldName: string) => void;
}> = ({ errorState, onFieldFocus }) => {
  const errorCount = Object.keys(errorState.fieldErrors).length + errorState.globalErrors.length;
  const warningCount = errorState.warnings.length;

  if (errorCount === 0 && warningCount === 0) return null;

  return (
    <div className="space-y-3">
      {/* Error Summary */}
      {errorCount > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">
                {errorCount === 1 ? '1 error' : `${errorCount} errors`} found
              </p>
              
              {/* Field errors */}
              {Object.entries(errorState.fieldErrors).length > 0 && (
                <div className="space-y-1">
                  {Object.entries(errorState.fieldErrors).map(([fieldName, error]) => (
                    <button
                      key={fieldName}
                      type="button"
                      onClick={() => onFieldFocus?.(fieldName)}
                      className="block text-left text-sm hover:underline focus:underline focus:outline-none"
                    >
                      • {error.message}
                    </button>
                  ))}
                </div>
              )}
              
              {/* Global errors */}
              {errorState.globalErrors.map((error, index) => (
                <p key={index} className="text-sm">• {error}</p>
              ))}
              
              {/* API errors */}
              {errorState.apiErrors.map((error, index) => (
                <div key={index} className="text-sm">
                  • {error.field ? `${error.field}: ` : ''}{error.message}
                  {error.code && (
                    <span className="text-xs text-muted-foreground ml-1">({error.code})</span>
                  )}
                </div>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Warning Summary */}
      {warningCount > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4 text-yellow-500" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium text-yellow-600">
                {warningCount === 1 ? '1 warning' : `${warningCount} warnings`}
              </p>
              {errorState.warnings.map((warning, index) => (
                <p key={index} className="text-sm text-yellow-600">• {warning}</p>
              ))}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

// Enhanced FormField component with comprehensive error handling
const FormField: React.FC<{
  name: string;
  schema: FormFieldSchema;
  control: Control<Record<string, unknown>>;
  errors: FieldErrors<Record<string, unknown>>;
  disabled?: boolean;
  isRequired?: boolean;
  validationError?: ValidationError;
  onFieldChange?: (fieldName: string, value: unknown) => void;
  formErrorState?: FormErrorState;
  allSchemaProperties?: Record<string, FormFieldSchema>;
}> = ({ 
  name, 
  schema, 
  control, 
  errors, 
  disabled = false, 
  isRequired = false,
  validationError,
  onFieldChange,
  formErrorState,
  allSchemaProperties
}) => {
  const fieldError = errors[name] || validationError;
  const hasError = !!fieldError;
  const hasWarning = validationError?.severity === 'warning';
  
  const getBorderColor = () => {
    if (hasError) {
      return hasWarning ? 'border-yellow-500 focus:border-yellow-500' : 'border-red-500 focus:border-red-500';
    }
    return '';
  };

  // Explicit LLM field detection - render LLMSelector for fields with form_field_type: "llm_provider"
  if (schema.form_field_type === 'llm_provider') {
    return (
      <div className={responsiveForm.field}>
        <Controller
          name={name}
          control={control}
          render={({ field: providerField }) => (
            <Controller
              name="model"
              control={control}
              render={({ field: modelField }) => {
                // Memoized callbacks to prevent re-renders
                const handleProviderChange = React.useCallback((provider: string) => {
                  providerField.onChange(provider);
                  onFieldChange?.(name, provider);
                }, [providerField.onChange, onFieldChange, name]);

                const handleModelChange = React.useCallback((model: string) => {
                  modelField.onChange(model);
                  onFieldChange?.('model', model);
                }, [modelField.onChange, onFieldChange]);

                return (
                  <LLMSelector
                    selectedProvider={providerField.value as string}
                    selectedModel={modelField.value as string}
                    onProviderChange={handleProviderChange}
                    onModelChange={handleModelChange}
                    disabled={disabled}
                    showLabels={true}
                    className="space-y-4"
                  />
                );
              }}
            />
          )}
        />
        
        {/* Show validation errors for provider or model */}
        {(errors[name] || formErrorState?.fieldErrors[name]) && (
          <ValidationErrorDisplay 
            error={formErrorState?.fieldErrors[name] || {
              field: name,
              message: typeof errors[name]?.message === 'string' ? errors[name].message : 'Provider selection error',
              type: 'custom',
              severity: 'error'
            }}
            className="mt-1"
          />
        )}
        
        {(errors.model || formErrorState?.fieldErrors.model) && (
          <ValidationErrorDisplay 
            error={formErrorState?.fieldErrors.model || {
              field: 'model',
              message: typeof errors.model?.message === 'string' ? errors.model.message : 'Model selection error',
              type: 'custom',
              severity: 'error'
            }}
            className="mt-1"
          />
        )}
      </div>
    );
  }

  // Skip rendering the model field if there's a corresponding LLM provider field
  if (name === 'model' && allSchemaProperties) {
    // Check if there's a provider field with llm_provider type
    const hasLLMProviderField = Object.values(allSchemaProperties).some(
      fieldSchema => fieldSchema.form_field_type === 'llm_provider'
    );
    if (hasLLMProviderField) {
      return null;
    }
  }

  const renderField = () => {
    switch (schema.form_field_type) {
      case 'textarea':
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <textarea
                name={field.name}
                value={String(field.value || '')}
                onBlur={field.onBlur}
                ref={field.ref}
                placeholder={schema.description || `Enter ${schema.title || name}`}
                disabled={disabled}
                className={cn(
                  "w-full min-h-[100px] px-3 py-2 text-sm border border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-vertical rounded-md",
                  getBorderColor()
                )}
                onChange={(e) => {
                  field.onChange(e.target.value);
                  onFieldChange?.(name, e.target.value);
                }}
              />
            )}
          />
        );
      
      case 'object':
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <textarea
                name={field.name}
                value={String(field.value || '')}
                onBlur={field.onBlur}
                ref={field.ref}
                placeholder={schema.description || `Enter JSON object for ${schema.title || name} (optional)`}
                disabled={disabled}
                className={cn(
                  "w-full min-h-[100px] px-3 py-2 text-sm border border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-vertical rounded-md font-mono",
                  getBorderColor()
                )}
                onChange={(e) => {
                  field.onChange(e.target.value);
                  onFieldChange?.(name, e.target.value);
                }}
              />
            )}
          />
        );
      
      case 'number':
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <Input
                name={field.name}
                value={field.value ? String(field.value) : ''}
                onBlur={field.onBlur}
                ref={field.ref}
                type="number"
                min={schema.minimum}
                max={schema.maximum}
                placeholder={schema.description || `Enter ${schema.title || name}`}
                disabled={disabled}
                className={cn(getBorderColor())}
                onChange={(e) => {
                  const value = e.target.value ? Number(e.target.value) : '';
                  field.onChange(value);
                  onFieldChange?.(name, value);
                }}
              />
            )}
          />
        );
      
      case 'checkbox':
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={Boolean(field.value)}
                  onChange={(e) => {
                    field.onChange(e.target.checked);
                    onFieldChange?.(name, e.target.checked);
                  }}
                  disabled={disabled}
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <Label htmlFor={name} className="text-sm text-muted-foreground">
                  {schema.description}
                </Label>
              </div>
            )}
          />
        );
      
      case 'select':
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <Select
                value={String(field.value || '')}
                onValueChange={(value) => {
                  field.onChange(value);
                  onFieldChange?.(name, value);
                }}
                disabled={disabled}
              >
                <SelectTrigger 
                  className={cn(getBorderColor())}
                >
                  <SelectValue placeholder={`Select ${schema.title || name}`} />
                </SelectTrigger>
                <SelectContent>
                  {schema.enum?.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        );
      
      default:
        return (
          <Controller
            name={name}
            control={control}
            render={({ field }) => (
              <Input
                name={field.name}
                value={String(field.value || '')}
                onBlur={field.onBlur}
                ref={field.ref}
                type={schema.form_field_type === 'password' ? 'password' : 
                      schema.form_field_type === 'email' ? 'email' :
                      schema.form_field_type === 'url' ? 'url' : 'text'}
                placeholder={schema.description || `Enter ${schema.title || name}`}
                disabled={disabled}
                className={cn(getBorderColor())}
                onChange={(e) => {
                  field.onChange(e.target.value);
                  onFieldChange?.(name, e.target.value);
                }}
              />
            )}
          />
        );
    }
  };
  
  return (
    <div className={responsiveForm.field}>
      <Label htmlFor={name} className={responsiveForm.label}>
        {schema.title || name} {isRequired && '*'}
      </Label>
      {renderField()}
      {(fieldError || validationError) && (
        <ValidationErrorDisplay 
          error={validationError || {
            field: name,
            message: typeof fieldError?.message === 'string' ? fieldError.message : `Invalid ${name}`,
            type: 'custom',
            severity: 'error'
          }}
          className="mt-1"
        />
      )}
    </div>
  );
};

// Skeleton loading component for form fields
const FormFieldSkeleton: React.FC = () => (
  <div className="space-y-2 animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
    <div className="h-10 bg-gray-200 rounded"></div>
  </div>
);

// Enhanced loading progress component
const SchemaLoadingProgress: React.FC<{ 
  loadingState: LoadingState; 
  onRetry?: () => void;
  agentName?: string;
}> = ({ loadingState, onRetry, agentName }) => {
  const getStageIcon = () => {
    switch (loadingState.stage) {
      case 'fetching':
        return <Wifi className="h-4 w-4 animate-pulse" />;
      case 'parsing':
        return <Zap className="h-4 w-4 animate-spin" />;
      case 'validating':
        return <CheckCircle className="h-4 w-4 animate-pulse" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStageDescription = () => {
    switch (loadingState.stage) {
      case 'fetching':
        return 'Connecting to agent and fetching schema...';
      case 'parsing':
        return 'Processing schema definition...';
      case 'validating':
        return 'Validating form structure...';
      default:
        return 'Preparing form...';
    }
  };

  if (loadingState.hasError) {
    const isAgentNotLoaded = loadingState.message.includes('is not currently active on the server');
    const isAgentNotFound = loadingState.message.includes('was not found');
    
    return (
      <div className="space-y-4">
        <Alert variant={isAgentNotFound ? "destructive" : "default"} 
               className={cn(isAgentNotLoaded && "border-orange-200 bg-orange-50")}>
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium">
                {isAgentNotLoaded ? 'Agent Not Available' : 
                 isAgentNotFound ? 'Agent Not Found' : 
                 'Failed to Load Schema'}
              </p>
              
              {/* Handle multi-line error messages */}
              {loadingState.message.includes('\n') ? (
                <div className="text-sm space-y-2">
                  {loadingState.message.split('\n').map((line, index) => (
                    <p key={index} className={line.startsWith('•') ? 'ml-2' : ''}>
                      {line}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="text-sm">{loadingState.message}</p>
              )}
              
              {agentName && (
                <p className="text-xs text-muted-foreground">
                  Agent: {agentName}
                </p>
              )}
              
              {/* Additional help for agent loading issues */}
              {isAgentNotLoaded && (
                <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                  <p className="font-medium mb-1">💡 Troubleshooting Tips:</p>
                  <ul className="space-y-1 ml-4 list-disc">
                    <li>Wait 30-60 seconds and try again</li>
                    <li>Check if other agents are working</li>
                    <li>Contact your system administrator if the issue persists</li>
                  </ul>
                </div>
              )}
            </div>
          </AlertDescription>
        </Alert>
        
        <div className="flex gap-2">
          {loadingState.canRetry && onRetry && (
            <Button
              variant={isAgentNotLoaded ? "default" : "outline"}
              onClick={onRetry}
              className="flex-1"
              disabled={loadingState.isLoading}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", loadingState.isLoading && "animate-spin")} />
              {loadingState.isLoading ? 'Retrying...' : 
               isAgentNotLoaded ? 'Try Again' : 'Retry Loading Schema'}
            </Button>
          )}
          
          {/* Go back button for non-retryable errors */}
          {!loadingState.canRetry && (
            <Button
              variant="outline"
              onClick={() => window.history.back()}
              className="flex-1"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {getStageIcon()}
        <div className="flex-1">
          <p className="text-sm font-medium">{loadingState.message}</p>
          <p className="text-xs text-muted-foreground">{getStageDescription()}</p>
          {agentName && (
            <p className="text-xs text-muted-foreground">Agent: {agentName}</p>
          )}
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Loading Progress</span>
          <span>{Math.round(loadingState.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${loadingState.progress}%` }}
          />
        </div>
      </div>
      
      {/* Form skeleton while loading */}
      <div className="space-y-4 pt-4">
        <FormFieldSkeleton />
        <FormFieldSkeleton />
        <FormFieldSkeleton />
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="animate-pulse">📝</div>
          <span>Preparing dynamic form fields based on agent schema...</span>
        </div>
      </div>
    </div>
  );
};

export function JobForm({ agentId, onJobCreated }: DynamicJobFormProps) {
  const toast = useToast();
  const [schemaData, setSchemaData] = useState<AgentSchemaResponse | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    stage: 'fetching',
    progress: 0,
    message: 'Initializing...',
    hasError: false,
    canRetry: false
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [formErrorState, setFormErrorState] = useState<FormErrorState>({
    hasErrors: false,
    fieldErrors: {},
    globalErrors: [],
    warnings: [],
    apiErrors: []
  });
  
  // Get the first available schema (most agents will have one primary schema)
  const primarySchema = schemaData?.schemas ? Object.values(schemaData.schemas)[0] : null;
  
  // Create Zod schema dynamically
  const zodSchema = primarySchema 
    ? createZodSchema(primarySchema.properties, primarySchema.required)
    : z.object({ title: z.string().min(1, 'Job title is required') });
  
  // Initialize react-hook-form
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
    getValues,
    clearErrors,
    setError: setFieldError
  } = useForm({
    resolver: zodResolver(zodSchema),
    mode: 'onChange', // Enable real-time validation
    defaultValues: {
      title: '',
      ...Object.fromEntries(
        Object.entries(primarySchema?.properties || {}).map(([key, schema]) => [
          key,
          schema.default || (schema.form_field_type === 'checkbox' ? false : '')
        ])
      )
    }
  });

  // Parse API validation errors
  const parseApiError = (errorMessage: string): ApiValidationError[] => {
    try {
      // Try to parse structured validation errors from API
      if (errorMessage.includes('validation')) {
        const errors: ApiValidationError[] = [];
        
        // Common API error patterns
        if (errorMessage.includes('required')) {
          const match = errorMessage.match(/field '([^']+)' is required/i);
          if (match) {
            errors.push({
              field: match[1],
              message: `${match[1]} is required`,
              code: 'REQUIRED_FIELD'
            });
          }
        }
        
        if (errorMessage.includes('invalid format')) {
          const match = errorMessage.match(/field '([^']+)' has invalid format/i);
          if (match) {
            errors.push({
              field: match[1],
              message: `Invalid format for ${match[1]}`,
              code: 'INVALID_FORMAT'
            });
          }
        }
        
        return errors.length > 0 ? errors : [{ message: errorMessage, code: 'VALIDATION_ERROR' }];
      }
      
      return [{ message: errorMessage, code: 'API_ERROR' }];
    } catch {
      return [{ message: errorMessage, code: 'UNKNOWN_ERROR' }];
    }
  };

  // Validate individual field
  const validateField = useCallback((fieldName: string, value: unknown) => {
    if (!primarySchema) return;
    
    const fieldSchema = primarySchema.properties[fieldName];
    if (!fieldSchema) return;
    
    const isRequired = primarySchema.required.includes(fieldName);
    const validationError = validateFieldValue(fieldName, value, fieldSchema, isRequired);
    
    setFormErrorState(prev => {
      const newFieldErrors = { ...prev.fieldErrors };
      
      if (validationError) {
        newFieldErrors[fieldName] = validationError;
      } else {
        delete newFieldErrors[fieldName];
      }
      
      return {
        ...prev,
        fieldErrors: newFieldErrors,
        hasErrors: Object.keys(newFieldErrors).length > 0
      };
    });
    
    // Clear react-hook-form error if our validation passed
    if (!validationError && errors[fieldName]) {
      clearErrors(fieldName);
    }
  }, [primarySchema, clearErrors, errors]);

  // Handle field changes with real-time validation
  const handleFieldChange = useCallback((fieldName: string, value: unknown) => {
    validateField(fieldName, value);
  }, [validateField]);

  // Validate entire form
  const validateForm = () => {
    if (!primarySchema) return false;
    
    const currentValues = getValues();
    const newFieldErrors: Record<string, ValidationError> = {};
    const warnings: string[] = [];
    
    // Validate all fields
    Object.entries(primarySchema.properties).forEach(([fieldName, fieldSchema]) => {
      const value = currentValues[fieldName];
      const isRequired = primarySchema.required.includes(fieldName);
      const validationError = validateFieldValue(fieldName, value, fieldSchema, isRequired);
      
      if (validationError) {
        if (validationError.severity === 'warning') {
          warnings.push(`${fieldName}: ${validationError.message}`);
        } else {
          newFieldErrors[fieldName] = validationError;
        }
      }
    });
    
    setFormErrorState(prev => ({
      ...prev,
      fieldErrors: newFieldErrors,
      warnings,
      hasErrors: Object.keys(newFieldErrors).length > 0
    }));
    
    return Object.keys(newFieldErrors).length === 0;
  };

  // Focus on field with error
  const focusOnField = (fieldName: string) => {
    const element = document.querySelector(`[name="${fieldName}"]`);
    if (element) {
      (element as HTMLElement).focus();
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Enhanced schema loading with progress tracking
  const loadSchema = useCallback(async (isRetry = false) => {
    if (isRetry) {
      setLoadingState(prev => ({ ...prev, isLoading: true, hasError: false, canRetry: false }));
    } else {
      setLoadingState({
        isLoading: true,
        stage: 'fetching',
        progress: 0,
        message: 'Loading form schema...',
        hasError: false,
        canRetry: false
      });
    }

    try {
      // Stage 1: Fetching schema
      setLoadingState(prev => ({ ...prev, stage: 'fetching', progress: 20, message: 'Fetching schema data...' }));
      
      await new Promise(resolve => setTimeout(resolve, 200));

      const data = await api.agents.getSchema(agentId);
      
      // Stage 2: Parsing
      setLoadingState(prev => ({ ...prev, stage: 'parsing', progress: 60, message: 'Parsing schema structure...' }));
      
      await new Promise(resolve => setTimeout(resolve, 150));

      if (!data.schemas || Object.keys(data.schemas).length === 0) {
        throw new Error(`Agent "${agentId}" has no available schemas. The agent may not be configured properly.`);
      }

      const schemaVersion = Object.keys(data.schemas)[0];
      const schema = data.schemas[schemaVersion];

      if (!schema || !schema.properties) {
        throw new Error(`Invalid schema format for agent "${agentId}". Missing required properties.`);
      }

      // Stage 3: Validating
      setLoadingState(prev => ({ ...prev, stage: 'validating', progress: 90, message: 'Validating form structure...' }));
      
      await new Promise(resolve => setTimeout(resolve, 100));

      setSchemaData(data);
      
      setLoadingState(prev => ({ 
        ...prev, 
        stage: 'ready', 
        progress: 100, 
        message: 'Form ready',
        isLoading: false,
        hasError: false,
        canRetry: false
      }));

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load schema';
      setLoadingState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        canRetry: true,
        message: errorMessage,
        progress: 0
      }));
      console.error('Schema loading error:', error);
    }
  }, [agentId]);
  
  // Load schema on mount or when agentId changes
  useEffect(() => {
    loadSchema();
  }, [agentId, loadSchema]);
  
  // Reset form when schema changes
  useEffect(() => {
    if (primarySchema) {
      const defaults = {
        title: '',
        ...Object.fromEntries(
          Object.entries(primarySchema.properties).map(([key, schema]) => [
            key,
            schema.default || (schema.form_field_type === 'checkbox' ? false : '')
          ])
        )
      };
      reset(defaults);
    }
  }, [primarySchema, reset]);
  
  const handleRetry = () => {
    loadSchema(true);
  };
  
  const onSubmit = async (data: Record<string, unknown>) => {
    // Pre-submission validation
    const isValid = validateForm();
    
    if (!isValid) {
      toast.error('Please fix the validation errors before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError('');
    setSuccess('');
    
    // Clear previous API errors
    setFormErrorState(prev => ({
      ...prev,
      apiErrors: [],
      globalErrors: []
    }));

    try {
      // Build job data - only include actual job data fields (no agent_identifier)
      const jobData: Record<string, unknown> = {
        title: data.title,
        ...Object.fromEntries(
          Object.entries(data).filter(([key]) => key !== 'title')
        )
      };
      
      // Transform optional fields properly for submission
      if (primarySchema) {
        Object.entries(primarySchema.properties).forEach(([fieldName, fieldSchema]) => {
          const value = jobData[fieldName];
          const isRequired = primarySchema.required.includes(fieldName);
          const schemaAnyOf = (fieldSchema as { anyOf?: Array<{ type: string }> }).anyOf;
          
          // Handle optional fields that can be null
          if (!isRequired && (value === '' || value === undefined)) {
            // Check if the field schema allows null (has anyOf with null type)
            const canBeNull = schemaAnyOf && schemaAnyOf.some((option) => option.type === 'null');
            
            if (canBeNull) {
              jobData[fieldName] = null;
            } else {
              // Remove empty optional fields that don't allow null
              delete jobData[fieldName];
            }
          }
          
          // Handle JSON/object fields that are sent as strings
          if (fieldSchema.form_field_type === 'object' || 
              (schemaAnyOf && schemaAnyOf.some((option) => option.type === 'object'))) {
            if (typeof value === 'string' && value.trim() !== '') {
              try {
                // Try to parse JSON string
                jobData[fieldName] = JSON.parse(value);
              } catch {
                // If parsing fails, leave as string (validation will catch this)
              }
            } else if (value === '' || value === undefined) {
              jobData[fieldName] = null;
            }
          }
        });
      }
      
      // Create the job using the correct API structure
      // Note: Backend expects agent_identifier at top level, not in data
      const jobRequest = {
        agent_identifier: agentId,
        data: {
          title: data.title as string,
          ...Object.fromEntries(
            Object.entries(jobData).filter(([key]) => key !== 'title')
          )
        },
        priority: 5,
        tags: [],
        metadata: {
          created_from: 'dynamic_form',
          agent_identifier: agentId,
          schema_version: schemaData?.schemas ? Object.keys(schemaData.schemas)[0] : 'unknown'
        }
      };
      
      const response = await api.jobs.create(jobRequest as Parameters<typeof api.jobs.create>[0]);
      
      setSuccess('Job created successfully!');
      toast.success(`Job created successfully! ID: ${response.job_id}`);
      onJobCreated(response.job_id);
      
      // Reset form and error state
      reset();
      setFormErrorState({
        hasErrors: false,
        fieldErrors: {},
        globalErrors: [],
        warnings: [],
        apiErrors: []
      });
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      const apiErrors = parseApiError(errorMessage);
      
      // Categorize API errors
      const fieldSpecificErrors: Record<string, ValidationError> = {};
      const globalErrors: string[] = [];
      
      apiErrors.forEach(apiError => {
        if (apiError.field && primarySchema?.properties[apiError.field]) {
          // Map API error to field-specific validation error
          fieldSpecificErrors[apiError.field] = {
            field: apiError.field,
            message: apiError.message,
            type: apiError.code === 'REQUIRED_FIELD' ? 'required' : 'custom',
            severity: 'error',
            suggestion: `Please check the ${apiError.field} field and try again.`
          };
          
          // Also set react-hook-form error for immediate UI feedback
          setFieldError(apiError.field, { 
            type: 'server', 
            message: apiError.message 
          });
        } else {
          globalErrors.push(apiError.message);
        }
      });
      
      setFormErrorState(prev => ({
        ...prev,
        fieldErrors: { ...prev.fieldErrors, ...fieldSpecificErrors },
        globalErrors,
        apiErrors,
        hasErrors: Object.keys(fieldSpecificErrors).length > 0 || globalErrors.length > 0
      }));
      
      setError(errorMessage);
      
      // Show appropriate toast based on error type
      if (Object.keys(fieldSpecificErrors).length > 0) {
        toast.error('Please fix the highlighted field errors and try again.');
      } else {
        toast.error('Failed to create job. Please try again.');
      }
      
      // Focus on first field with error
      const firstErrorField = Object.keys(fieldSpecificErrors)[0];
      if (firstErrorField) {
        setTimeout(() => focusOnField(firstErrorField), 100);
      }
      
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show loading progress while schema is loading
  if (loadingState.isLoading || loadingState.hasError) {
    return (
      <div className="space-y-4">
        <SchemaLoadingProgress 
          loadingState={loadingState} 
          onRetry={handleRetry}
          agentName={agentId}
        />
        
        {/* Show fallback form option for agent loading issues */}
        {loadingState.hasError && 
         loadingState.message.includes('is not currently active on the server') && (
          <div className="mt-6 p-4 border border-dashed border-gray-300 rounded-lg bg-gray-50">
            <div className="text-center space-y-3">
              <p className="text-sm font-medium text-gray-700">
                Unable to load dynamic form
              </p>
              <p className="text-xs text-gray-600">
                You can still create a basic job with just a title while the agent is starting up.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // Set a minimal schema to allow basic job creation
                  setSchemaData({
                    status: 'fallback',
                    agent_id: agentId,
                    agent_name: agentId,
                    description: 'Basic job creation (agent schema unavailable)',
                    instance_available: false,
                    available_models: ['BasicJobData'],
                    schemas: {
                      BasicJobData: {
                        model_name: 'BasicJobData',
                        model_class: 'BasicJobData',
                        title: 'Basic Job Input',
                        description: 'Basic job creation form',
                        type: 'object',
                        properties: {
                          title: {
                            title: 'Job Title',
                            type: 'string',
                            form_field_type: 'text',
                            description: 'Enter a descriptive title for this job'
                          }
                        },
                        required: ['title']
                      }
                    }
                  });
                  setLoadingState({
                    isLoading: false,
                    stage: 'ready',
                    progress: 100,
                    message: 'Using basic form mode',
                    hasError: false,
                    canRetry: true
                  });
                }}
                className="text-xs"
              >
                Use Basic Form
              </Button>
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // No schema available
  if (!primarySchema) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Create New Job</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              No job data schema available for this agent. Please ensure the agent is properly configured.
            </AlertDescription>
          </Alert>
          
          <Button
            variant="outline"
            onClick={handleRetry}
            className="w-full mt-4"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Reload Schema
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg sm:text-xl">
          Create New Job
          {schemaData?.agent_name && (
            <span className="text-sm font-normal text-muted-foreground ml-2">
              ({schemaData.agent_name})
            </span>
          )}
        </CardTitle>
        {schemaData?.description && (
          <p className="text-sm text-muted-foreground mt-2">
            {schemaData.description}
          </p>
        )}
      </CardHeader>
      <hr />
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className={responsiveForm.container}>
          {/* Error Summary */}
          <ErrorSummary 
            errorState={formErrorState}
            onFieldFocus={focusOnField}
          />

          {/* Job Title - Always present */}
          <div className={responsiveForm.field}>
            <Label htmlFor="title" className={responsiveForm.label}>
              Job Title *
            </Label>
            <Controller
              name="title"
              control={control}
              render={({ field }) => (
            <Input
                  {...field}
              placeholder="Enter a descriptive title for your job"
                  disabled={isSubmitting}
              className={cn(
                responsiveForm.input,
                    (errors.title || formErrorState.fieldErrors.title) && 'border-red-500 focus:border-red-500'
                  )}
                  onChange={(e) => {
                    field.onChange(e.target.value);
                    handleFieldChange('title', e.target.value);
                  }}
                />
              )}
            />
            {(errors.title || formErrorState.fieldErrors.title) && (
              <ValidationErrorDisplay 
                error={formErrorState.fieldErrors.title || {
                  field: 'title',
                  message: typeof errors.title?.message === 'string' ? errors.title.message : 'Job title is required',
                  type: 'required',
                  severity: 'error'
                }}
                className="mt-1"
              />
            )}
          </div>

          {/* Dynamic fields based on schema */}
          {Object.entries(primarySchema.properties).map(([fieldName, fieldSchema]) => (
            <FormField
              key={fieldName}
              name={fieldName}
              schema={fieldSchema}
              control={control}
              errors={errors}
              disabled={isSubmitting}
              isRequired={primarySchema.required.includes(fieldName)}
              validationError={formErrorState.fieldErrors[fieldName]}
              onFieldChange={handleFieldChange}
              formErrorState={formErrorState}
              allSchemaProperties={primarySchema.properties}
            />
          ))}

          {/* Global Error Alert */}
          {error && !formErrorState.hasErrors && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isSubmitting || formErrorState.hasErrors}
            className={cn("w-full touch-manipulation", responsiveForm.button)}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Job...
              </>
            ) : formErrorState.hasErrors ? (
              'Fix Errors to Continue'
            ) : (
              'Create Job'
            )}
          </Button>
          
          {/* Form validation status */}
          {formErrorState.hasErrors && (
            <div className="text-center text-sm text-muted-foreground mt-2">
              <AlertCircle className="h-3 w-3 inline mr-1" />
              Please resolve the validation errors above to submit the form.
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
} 