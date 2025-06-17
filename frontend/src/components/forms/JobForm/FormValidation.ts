import { z } from 'zod';
import type { FormFieldSchema } from '@/lib/models';
import type { ValidationError, ApiValidationError } from './types';

// ============================================================================
// CENTRALIZED FIELD INFERENCE SYSTEM
// ============================================================================

interface FieldInference {
  fieldType: string;
  constraints: {
    minimum?: number;
    maximum?: number;
    minLength?: number;
    maxLength?: number;
  };
  isOptional: boolean;
}

/**
 * Central field inference from Pydantic schema
 * Used by FormField, validation, and Zod schema creation
 */
export const inferFieldFromSchema = (schema: FormFieldSchema, requiredFields: string[], fieldName: string): FieldInference => {
  let fieldType = schema.type;
  let constraints = {
    minimum: schema.minimum,
    maximum: schema.maximum,
    minLength: schema.minLength,
    maxLength: schema.maxLength
  };
  
  // Handle Optional fields (anyOf with type and null)
  let isOptional = !requiredFields.includes(fieldName);
  if (schema.anyOf) {
    // Find the actual type (not null)
    const actualType = schema.anyOf.find((type: any) => type.type !== 'null');
    if (actualType) {
      fieldType = actualType.type;
      // Extract constraints from the actual type
      constraints = {
        minimum: (typeof actualType.minimum === 'number') ? actualType.minimum : constraints.minimum,
        maximum: (typeof actualType.maximum === 'number') ? actualType.maximum : constraints.maximum,
        minLength: (typeof actualType.minLength === 'number') ? actualType.minLength : constraints.minLength,
        maxLength: (typeof actualType.maxLength === 'number') ? actualType.maxLength : constraints.maxLength
      };
    }
    // anyOf always means optional (can be null)
    isOptional = true;
  }
  
  // Determine UI field type
  let uiFieldType = 'input';
  
  if (fieldType === 'boolean') {
    uiFieldType = 'checkbox';
  } else if (fieldType === 'number' || fieldType === 'integer') {
    uiFieldType = 'number';
  } else if (fieldType === 'array') {
    uiFieldType = 'array';
  } else if (schema.enum && schema.enum.length > 0) {
    uiFieldType = 'select';
  } else if (fieldType === 'object') {
    uiFieldType = 'object';
  } else if (fieldType === 'string') {
    // String field type detection
    if (schema.format === 'email') {
      uiFieldType = 'email';
    } else if (schema.format === 'uri' || schema.format === 'url') {
      uiFieldType = 'url';
    } else if (schema.title?.toLowerCase().includes('password')) {
      uiFieldType = 'password';
    } else if (
      (constraints.maxLength && constraints.maxLength > 100) ||
      (schema.description && schema.description.length > 100) ||
      (schema.description?.toLowerCase().includes('examples:'))
    ) {
      uiFieldType = 'textarea';
    } else {
      uiFieldType = 'input';
    }
  }
  
  return {
    fieldType: uiFieldType,
    constraints,
    isOptional
  };
};

// ============================================================================
// SIMPLIFIED VALIDATION
// ============================================================================

// Error recovery suggestions
export const getErrorSuggestion = (error: ValidationError, schema: FormFieldSchema): string => {
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
export const validateFieldValue = (
  fieldName: string, 
  value: unknown, 
  schema: FormFieldSchema, 
  requiredFields: string[]
): ValidationError | null => {
  // Use central inference system with full required fields array
  const inference = inferFieldFromSchema(schema, requiredFields, fieldName);
  const isRequired = requiredFields.includes(fieldName);
  
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

  // Skip validation for empty optional fields (including null for Optional fields)
  if (inference.isOptional && (value === '' || value === null || value === undefined)) {
    return null;
  }

  // Type-specific validation using inferred field type
  switch (inference.fieldType) {
    case 'email': {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(String(value))) {
        return {
          field: fieldName,
          message: 'Invalid email format',
          type: 'format',
          severity: 'error',
          suggestion: 'Please enter a valid email address (e.g., user@example.com)'
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
          suggestion: 'Please enter a valid URL (e.g., https://example.com)'
        };
      }
      break;

    case 'object': {
      if (value && typeof value === 'string' && value.trim() !== '') {
        try {
          const parsed = JSON.parse(value);
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
            suggestion: 'Check your JSON syntax. Example: {"key": "value"}'
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
      if (inference.constraints.minimum !== undefined && numValue < inference.constraints.minimum) {
        return {
          field: fieldName,
          message: `Must be at least ${inference.constraints.minimum}`,
          type: 'range',
          severity: 'error'
        };
      }
      if (inference.constraints.maximum !== undefined && numValue > inference.constraints.maximum) {
        return {
          field: fieldName,
          message: `Must not exceed ${inference.constraints.maximum}`,
          type: 'range',
          severity: 'error'
        };
      }
      break;
    }

    case 'textarea':
    case 'input': {
      const strValue = String(value);
      if (inference.constraints.minLength !== undefined && strValue.length < inference.constraints.minLength) {
        return {
          field: fieldName,
          message: `Must be at least ${inference.constraints.minLength} characters`,
          type: 'constraint',
          severity: 'error'
        };
      }
      if (inference.constraints.maxLength !== undefined && strValue.length > inference.constraints.maxLength) {
        return {
          field: fieldName,
          message: `Must not exceed ${inference.constraints.maxLength} characters`,
          type: 'constraint',
          severity: 'error'
        };
      }
      break;
    }
  }

  return null;
};

// Helper function to create Zod schema from JSON schema
export const createZodSchema = (schema: Record<string, FormFieldSchema>, required: string[]) => {
  const shape: Record<string, z.ZodTypeAny> = {};
  
  // Always require title
  shape.title = z.string().min(1, 'Job title is required');
  
  for (const [fieldName, fieldSchema] of Object.entries(schema)) {
    const inference = inferFieldFromSchema(fieldSchema, required, fieldName);
    let zodField: z.ZodTypeAny;
    
    switch (inference.fieldType) {
      case 'number':
        zodField = z.number();
        if (inference.constraints.minimum !== undefined) {
          zodField = (zodField as z.ZodNumber).min(inference.constraints.minimum);
        }
        if (inference.constraints.maximum !== undefined) {
          zodField = (zodField as z.ZodNumber).max(inference.constraints.maximum);
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
        if (inference.constraints.minLength) {
          zodField = (zodField as z.ZodString).min(inference.constraints.minLength);
        }
        if (inference.constraints.maxLength) {
          zodField = (zodField as z.ZodString).max(inference.constraints.maxLength);
        }
        if (fieldSchema.pattern) {
          zodField = (zodField as z.ZodString).regex(new RegExp(fieldSchema.pattern));
        }
        break;
    }
    
    // Make field optional based on inference
    if (inference.isOptional) {
      // For Pydantic Optional fields (anyOf with null), use nullish() to allow both null and undefined
      zodField = zodField.nullish();
    }
    
    shape[fieldName] = zodField;
  }
  
  return z.object(shape);
};

// Parse API error messages into structured format
export const parseApiError = (errorMessage: string): ApiValidationError[] => {
  try {
    // Try to parse as JSON first
    const parsed = JSON.parse(errorMessage);
    
    if (Array.isArray(parsed)) {
      return parsed.map((error: any) => ({
        field: error.loc ? error.loc.join('.') : error.field,
        message: error.msg || error.message || String(error),
        code: error.type || error.code,
        details: error
      }));
    }
    
    if (parsed.detail && Array.isArray(parsed.detail)) {
      return parsed.detail.map((error: any) => ({
        field: error.loc ? error.loc.join('.') : error.field,
        message: error.msg || error.message || String(error),
        code: error.type || error.code,
        details: error
      }));
    }
    
    if (parsed.detail) {
      return [{
        message: parsed.detail,
        details: parsed
      }];
    }
    
    return [{
      message: String(parsed),
      details: parsed
    }];
    
  } catch {
    // Not JSON, treat as plain text
    // Try to extract field-specific errors from common formats
    const fieldErrorRegex = /(\w+):\s*(.+?)(?=\s*\w+:|$)/g;
    const errors: ApiValidationError[] = [];
    let match;
    
    while ((match = fieldErrorRegex.exec(errorMessage)) !== null) {
      errors.push({
        field: match[1],
        message: match[2].trim()
      });
    }
    
    if (errors.length === 0) {
      errors.push({
        message: errorMessage
      });
    }
    
    return errors;
  }
}; 