import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import type { ErrorSummaryProps } from './types';

// Error summary component for displaying multiple validation errors
export const ErrorSummary: React.FC<ErrorSummaryProps> = ({ errorState, onFieldFocus }) => {
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