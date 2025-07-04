import type { Control, FieldErrors } from 'react-hook-form';
import type { FormFieldSchema } from '@/lib/types';

// Edit mode configuration
export interface EditMode {
  scheduleId: string;
  initialData: Record<string, unknown>;
}

// JobForm component types and interfaces
export interface DynamicJobFormProps {
  agentId: string;
  onJobCreated: (jobId: string) => void;
  editMode?: EditMode;
}

// Enhanced loading states
export interface LoadingState {
  isLoading: boolean;
  stage: 'fetching' | 'parsing' | 'validating' | 'ready';
  progress: number;
  message: string;
  hasError: boolean;
  canRetry: boolean;
}

// Enhanced error handling types
export interface ValidationError {
  field: string;
  message: string;
  type: 'required' | 'format' | 'range' | 'constraint' | 'custom';
  severity: 'error' | 'warning';
  suggestion?: string;
}

export interface FormErrorState {
  hasErrors: boolean;
  fieldErrors: Record<string, ValidationError>;
  globalErrors: string[];
  warnings: string[];
  apiErrors: ApiValidationError[];
}

export interface ApiValidationError {
  field?: string;
  message: string;
  code?: string;
  details?: unknown;
}

export interface FormFieldProps {
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
}

export interface ValidationErrorDisplayProps {
  error: ValidationError;
  className?: string;
}

export interface ErrorSummaryProps {
  errorState: FormErrorState;
  onFieldFocus?: (fieldName: string) => void;
}

export interface SchemaLoadingProgressProps {
  loadingState: LoadingState;
  onRetry?: () => void;
  agentName?: string;
} 