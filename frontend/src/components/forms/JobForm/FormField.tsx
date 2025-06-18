import React from 'react';
import { Controller } from 'react-hook-form';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { ValidationErrorDisplay } from './ValidationErrorDisplay';
import { inferFieldFromSchema } from './FormValidation';
import type { FormFieldSchema } from '@/lib/types';
import type { 
  ValidationError
} from './types';

interface FormFieldProps {
  name: string;
  schema: FormFieldSchema;
  control: any; // react-hook-form control
  errors: Record<string, any>;
  disabled: boolean;
  isRequired: boolean;
  validationError?: ValidationError;
  onFieldChange: (fieldName: string, value: unknown) => void;
}

export const FormField: React.FC<FormFieldProps> = ({
  name,
  schema,
  control,
  errors,
  disabled,
  isRequired,
  validationError,
  onFieldChange
}) => {
  const fieldError = errors[name];
  const hasError = !!(fieldError || validationError);

  // Use centralized inference system
  const inference = inferFieldFromSchema(schema, isRequired ? [name] : [], name);
  const fieldType = schema.form_field_type || inference.fieldType;

  // Get field description/help text
  const getFieldDescription = () => {
    let description = schema.description || '';
    
    // Add format hints for specific field types
    if (schema.form_field_type === 'email') {
      description += description ? ' ' : '';
      description += 'Enter a valid email address (e.g., user@example.com)';
    } else if (schema.form_field_type === 'url') {
      description += description ? ' ' : '';
      description += 'Enter a valid URL (e.g., https://example.com)';
    } else if (schema.form_field_type === 'object') {
      description += description ? ' ' : '';
      description += 'Enter valid JSON (e.g., {"key": "value"})';
    }
    
    // Add constraints info
    if (schema.minimum !== undefined || schema.maximum !== undefined) {
      description += description ? ' ' : '';
      if (schema.minimum !== undefined && schema.maximum !== undefined) {
        description += `Value must be between ${schema.minimum} and ${schema.maximum}.`;
      } else if (schema.minimum !== undefined) {
        description += `Minimum value: ${schema.minimum}.`;
      } else if (schema.maximum !== undefined) {
        description += `Maximum value: ${schema.maximum}.`;
      }
    }
    
    if (schema.minLength !== undefined || schema.maxLength !== undefined) {
      description += description ? ' ' : '';
      if (schema.minLength !== undefined && schema.maxLength !== undefined) {
        description += `Length must be between ${schema.minLength} and ${schema.maxLength} characters.`;
      } else if (schema.minLength !== undefined) {
        description += `Minimum length: ${schema.minLength} characters.`;
      } else if (schema.maxLength !== undefined) {
        description += `Maximum length: ${schema.maxLength} characters.`;
      }
    }
    
    return description;
  };

  // Render field based on type
  const renderField = (field: any) => {
    const baseProps = {
      ...field,
      disabled,
      className: cn(
        "w-full",
        hasError && "border-red-500 focus:border-red-500"
      )
    };

    switch (fieldType) {
      case 'textarea':
        return (
          <Textarea
            {...baseProps}
            placeholder={schema.description || `Enter ${schema.title?.toLowerCase() || name}`}
            rows={4}
            onChange={(e) => {
              field.onChange(e.target.value);
              onFieldChange(name, e.target.value);
            }}
          />
        );

      case 'number':
        return (
          <Input
            {...baseProps}
            type="number"
            min={inference.constraints.minimum}
            max={inference.constraints.maximum}
            step="any"
            placeholder={`Enter ${schema.title?.toLowerCase() || name}`}
            onChange={(e) => {
              const value = e.target.value ? Number(e.target.value) : '';
              field.onChange(value);
              onFieldChange(name, value);
            }}
          />
        );

      case 'email':
        return (
          <Input
            {...baseProps}
            type="email"
            placeholder="user@example.com"
            onChange={(e) => {
              field.onChange(e.target.value);
              onFieldChange(name, e.target.value);
            }}
          />
        );

      case 'url':
        return (
          <Input
            {...baseProps}
            type="url"
            placeholder="https://example.com"
            onChange={(e) => {
              field.onChange(e.target.value);
              onFieldChange(name, e.target.value);
            }}
          />
        );

      case 'password':
        return (
          <Input
            {...baseProps}
            type="password"
            placeholder="Enter password"
            onChange={(e) => {
              field.onChange(e.target.value);
              onFieldChange(name, e.target.value);
            }}
          />
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <input
              id={name}
              type="checkbox"
              checked={field.value || false}
              onChange={(e) => {
                field.onChange(e.target.checked);
                onFieldChange(name, e.target.checked);
              }}
              disabled={disabled}
              className={cn(
                "h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary",
                hasError && "border-red-500"
              )}
            />
            <Label 
              htmlFor={name}
              className={cn(
                "text-sm font-normal cursor-pointer",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {schema.title || name}
            </Label>
          </div>
        );

      case 'select':
        if (!schema.enum || schema.enum.length === 0) {
          return (
            <div className="text-sm text-muted-foreground p-2 border rounded">
              No options available for this field
            </div>
          );
        }

        return (
          <Select
            value={field.value || ''}
            onValueChange={(value) => {
              field.onChange(value);
              onFieldChange(name, value);
            }}
            disabled={disabled}
          >
            <SelectTrigger className={cn(hasError && "border-red-500")}>
              <SelectValue placeholder={`Select ${schema.title?.toLowerCase() || name}`} />
            </SelectTrigger>
            <SelectContent>
              {schema.enum.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'object':
        return (
          <div className="space-y-2">
            <Textarea
              {...baseProps}
              placeholder='{"key": "value"}'
              rows={6}
              className={cn(
                "font-mono text-sm",
                hasError && "border-red-500 focus:border-red-500"
              )}
              onChange={(e) => {
                field.onChange(e.target.value);
                onFieldChange(name, e.target.value);
              }}
            />
            <div className="text-xs text-muted-foreground">
              💡 Tip: Use valid JSON format with double quotes around keys and string values
            </div>
          </div>
        );

      case 'array':
        return (
          <div className="space-y-2">
            <Textarea
              {...baseProps}
              placeholder='["item1", "item2", "item3"]'
              rows={4}
              className={cn(
                "font-mono text-sm",
                hasError && "border-red-500 focus:border-red-500"
              )}
              onChange={(e) => {
                field.onChange(e.target.value);
                onFieldChange(name, e.target.value);
              }}
            />
            <div className="text-xs text-muted-foreground">
              💡 Tip: Use valid JSON array format
            </div>
          </div>
        );

      case 'hidden':
        return (
          <Input
            {...baseProps}
            type="hidden"
          />
        );

      default:
        // Default to text input
        return (
          <Input
            {...baseProps}
            type="text"
            placeholder={`Enter ${schema.title?.toLowerCase() || name}`}
            minLength={schema.minLength}
            maxLength={schema.maxLength}
            pattern={schema.pattern}
            onChange={(e) => {
              field.onChange(e.target.value);
              onFieldChange(name, e.target.value);
            }}
          />
        );
    }
  };

  // Don't render hidden fields in the UI
  if (fieldType === 'hidden') {
    return (
      <Controller
        name={name}
        control={control}
        render={({ field }) => renderField(field)}
      />
    );
  }

  const fieldDescription = getFieldDescription();

  return (
    <div className="space-y-2">
      {/* Field Label */}
      {fieldType !== 'checkbox' && (
        <Label 
          htmlFor={name}
          className={cn(
            "text-sm font-medium",
            isRequired && "after:content-['*'] after:ml-0.5 after:text-red-500",
            disabled && "opacity-50"
          )}
        >
          {schema.title || name}
        </Label>
      )}

      {/* Field Description */}
      {fieldDescription && fieldType !== 'textarea' && (
        <p className="text-xs text-muted-foreground">
          {fieldDescription}
        </p>
      )}

      {/* Field Input */}
      <Controller
        name={name}
        control={control}
        render={({ field }) => renderField(field)}
      />

      {/* Error Display */}
      {validationError && (
        <ValidationErrorDisplay error={validationError} />
      )}
      
      {fieldError && !validationError && (
        <ValidationErrorDisplay 
          error={{
            field: name,
            message: String(fieldError.message || fieldError),
            type: 'custom',
            severity: 'error'
          }}
        />
      )}

      {/* Additional field-specific help */}
      {fieldType === 'object' && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
            JSON Object Examples
          </summary>
          <div className="mt-2 p-2 bg-muted rounded text-muted-foreground font-mono space-y-1">
            <div>Simple: {`{"name": "value"}`}</div>
            <div>Multiple: {`{"key1": "value1", "key2": "value2"}`}</div>
            <div>Nested: {`{"user": {"name": "John", "age": 30}}`}</div>
          </div>
        </details>
      )}

      {fieldType === 'array' && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
            JSON Array Examples
          </summary>
          <div className="mt-2 p-2 bg-muted rounded text-muted-foreground font-mono space-y-1">
            <div>Strings: {`["item1", "item2", "item3"]`}</div>
            <div>Numbers: {`[1, 2, 3, 4, 5]`}</div>
            <div>Objects: {`[{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]`}</div>
          </div>
        </details>
      )}
    </div>
  );
}; 