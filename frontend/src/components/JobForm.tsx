import React, { useState } from 'react';
import { useToast } from '@/components/ui/toast';
import { responsiveForm, responsivePadding } from '@/lib/responsive';
import { api, handleApiError, type CreateJobRequest } from '@/lib/api';
import type { AgentType, JobData } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface JobFormProps {
  onJobCreated: (jobId: string) => void;
}

interface JobFormData {
  title: string;
  agentType: AgentType | '';
  inputText: string;
  inputUrl: string;
  parameters: string;
}

const agentTypes = [
  { 
    value: 'text_processing', 
    label: 'Text Processing', 
    description: 'Process and analyze text content with NLP operations' 
  },
  { 
    value: 'summarization', 
    label: 'Summarization', 
    description: 'Summarize text, audio, or video content' 
  },
  { 
    value: 'web_scraping', 
    label: 'Web Scraping', 
    description: 'Extract data from websites and web pages' 
  },
];

export function JobForm({ onJobCreated }: JobFormProps) {
  const toast = useToast();
  const [formData, setFormData] = useState<JobFormData>({
    title: '',
    agentType: '',
    inputText: '',
    inputUrl: '',
    parameters: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    }

    if (!formData.agentType) {
      errors.agentType = 'Agent type is required';
    }

    // Validate based on agent type
    if (formData.agentType === 'text_processing') {
      if (!formData.inputText.trim()) {
        errors.inputText = 'Input text is required for text processing';
      }
    } else if (formData.agentType === 'web_scraping') {
      if (!formData.inputUrl.trim()) {
        errors.inputUrl = 'URL is required for web scraping';
      } else {
        try {
          new URL(formData.inputUrl);
        } catch {
          errors.inputUrl = 'Please enter a valid URL';
        }
      }
    } else if (formData.agentType === 'summarization') {
      if (!formData.inputText.trim() && !formData.inputUrl.trim()) {
        errors.inputText = 'Either text input or URL is required for summarization';
        errors.inputUrl = 'Either text input or URL is required for summarization';
      }
      
      // If URL is provided, validate it
      if (formData.inputUrl.trim()) {
        try {
          new URL(formData.inputUrl);
        } catch {
          errors.inputUrl = 'Please enter a valid URL';
        }
      }
    }

    // Validate parameters if provided
    if (formData.parameters.trim()) {
      try {
        JSON.parse(formData.parameters);
      } catch {
        errors.parameters = 'Parameters must be valid JSON';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof JobFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const buildJobData = (): JobData => {
    const baseData = {
      agent_type: formData.agentType as AgentType,
      title: formData.title.trim(),
    };

    // Parse additional parameters if provided
    let additionalParams: Record<string, any> = {};
    if (formData.parameters.trim()) {
      try {
        additionalParams = JSON.parse(formData.parameters);
      } catch {
        // This should be caught by validation, but just in case
        additionalParams = {};
      }
    }

    // Build agent-specific job data
    switch (formData.agentType) {
      case 'text_processing':
        return {
          ...baseData,
          agent_type: 'text_processing',
          input_text: formData.inputText.trim(),
          operation: additionalParams.operation || 'sentiment_analysis',
          language: additionalParams.language || 'en',
          max_length: additionalParams.max_length,
          temperature: additionalParams.temperature,
        };

      case 'summarization':
        const summarizationData: any = {
          ...baseData,
          agent_type: 'summarization',
          max_summary_length: additionalParams.max_summary_length || 200,
          format: additionalParams.format || 'paragraph',
          language: additionalParams.language || 'en',
          include_quotes: additionalParams.include_quotes || false,
        };

        // Add input text or URL based on what's provided
        if (formData.inputText.trim()) {
          summarizationData.input_text = formData.inputText.trim();
        }
        if (formData.inputUrl.trim()) {
          summarizationData.input_url = formData.inputUrl.trim();
        }

        return summarizationData;

      case 'web_scraping':
        return {
          ...baseData,
          agent_type: 'web_scraping',
          input_url: formData.inputUrl.trim(),
          selectors: additionalParams.selectors || [],
          max_pages: additionalParams.max_pages || 1,
          wait_time: additionalParams.wait_time || 2,
          follow_links: additionalParams.follow_links || false,
          extract_images: additionalParams.extract_images || false,
          extract_metadata: additionalParams.extract_metadata || true,
        };

      default:
        throw new Error(`Unknown agent type: ${formData.agentType}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setError('');
    setSuccess('');

    try {
      const jobData = buildJobData();
      
      const createRequest: CreateJobRequest = {
        data: jobData,
        priority: 'normal',
        tags: [],
        metadata: {
          created_from: 'web_ui',
          user_agent: navigator.userAgent,
        },
      };

      const response = await api.jobs.create(createRequest);
      
      setSuccess('Job created successfully!');
      toast.success('Job created successfully!', {
        title: 'Success',
      });
      
      // Reset form
      setFormData({
        title: '',
        agentType: '',
        inputText: '',
        inputUrl: '',
        parameters: '',
      });
      
      // Notify parent component
      onJobCreated(response.job_id);
      
    } catch (err: any) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      toast.error(`Failed to create job: ${errorMessage}`, {
        title: 'Error',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getInputDescription = () => {
    switch (formData.agentType) {
      case 'text_processing':
        return 'Enter the text you want to process and analyze. The system can perform sentiment analysis, entity extraction, and other NLP operations.';
      case 'summarization':
        return 'Enter text to summarize, or provide a URL to content (text, audio, or video). You can specify additional parameters like summary length and format.';
      case 'web_scraping':
        return 'Enter the URL of the website you want to scrape data from. You can specify CSS selectors and other parameters to control the extraction.';
      default:
        return 'Select an agent type to see input requirements and descriptions.';
    }
  };

  const getParametersPlaceholder = (agentType: string) => {
    switch (agentType) {
      case 'text_processing':
        return '{\n  "operation": "sentiment_analysis",\n  "language": "en",\n  "max_length": 1000,\n  "temperature": 0.7\n}';
      case 'summarization':
        return '{\n  "max_summary_length": 200,\n  "format": "bullet_points",\n  "language": "en",\n  "include_quotes": true\n}';
      case 'web_scraping':
        return '{\n  "selectors": ["h1", ".content", "p"],\n  "max_pages": 5,\n  "wait_time": 3,\n  "follow_links": false,\n  "extract_images": true\n}';
      default:
        return '{\n  "key": "value"\n}';
    }
  };

  const shouldShowInput = (type: 'text' | 'url') => {
    if (formData.agentType === 'text_processing') return type === 'text';
    if (formData.agentType === 'web_scraping') return type === 'url';
    if (formData.agentType === 'summarization') return true;
    return false;
  };

  const getInputLabel = (type: 'text' | 'url') => {
    if (formData.agentType === 'summarization') {
      return type === 'text' 
        ? 'Input Text (optional if URL provided)' 
        : 'Input URL (optional if text provided)';
    }
    return type === 'text' ? 'Input Text *' : 'Input URL *';
  };

  return (
    <Card className="w-full">
      <CardHeader className={responsivePadding.card}>
        <CardTitle className="text-lg sm:text-xl">Create New Job</CardTitle>
      </CardHeader>
      <CardContent className={responsivePadding.card}>
        <form onSubmit={handleSubmit} className={responsiveForm.container}>
          {/* Job Title */}
          <div className={responsiveForm.field}>
            <Label htmlFor="title" className={responsiveForm.label}>
              Job Title *
            </Label>
            <Input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="Enter a descriptive title for your job"
              className={cn(
                responsiveForm.input,
                validationErrors.title && 'border-red-500 focus:border-red-500'
              )}
              disabled={isSubmitting}
            />
            {validationErrors.title && (
              <p className="text-sm text-red-500 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                {validationErrors.title}
              </p>
            )}
          </div>

          {/* Agent Type */}
          <div className={responsiveForm.field}>
            <Label htmlFor="agentType" className={responsiveForm.label}>
              Agent Type *
            </Label>
            <Select
              value={formData.agentType}
              onValueChange={(value) => handleInputChange('agentType', value)}
              disabled={isSubmitting}
            >
              <SelectTrigger 
                className={cn(
                  responsiveForm.input,
                  validationErrors.agentType && 'border-red-500 focus:border-red-500'
                )}
              >
                <SelectValue placeholder="Select an agent type" />
              </SelectTrigger>
              <SelectContent>
                {agentTypes.map((agent) => (
                  <SelectItem key={agent.value} value={agent.value}>
                    <div className="space-y-1">
                      <div className="font-medium">{agent.label}</div>
                      <div className="text-xs text-muted-foreground">{agent.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {validationErrors.agentType && (
              <p className="text-sm text-red-500 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                {validationErrors.agentType}
              </p>
            )}
          </div>

          {/* Input Description */}
          {formData.agentType && (
            <div className="bg-muted/50 p-3 sm:p-4 rounded-lg">
              <p className="text-sm text-muted-foreground">{getInputDescription()}</p>
            </div>
          )}

          {/* Text Input */}
          {shouldShowInput('text') && (
            <div className={responsiveForm.field}>
              <Label htmlFor="inputText" className={responsiveForm.label}>
                {getInputLabel('text')}
              </Label>
              <textarea
                id="inputText"
                value={formData.inputText}
                onChange={(e) => handleInputChange('inputText', e.target.value)}
                placeholder={
                  formData.agentType === 'text_processing' 
                    ? "Enter the text you want to process and analyze..."
                    : "Enter the text you want to summarize..."
                }
                className={cn(
                  "w-full min-h-[120px] px-4 py-3 text-base sm:min-h-[100px] sm:px-3 sm:py-2 sm:text-sm border border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-vertical rounded-md",
                  validationErrors.inputText && 'border-red-500 focus:border-red-500'
                )}
                disabled={isSubmitting}
              />
              {validationErrors.inputText && (
                <p className="text-sm text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="h-3 w-3" />
                  {validationErrors.inputText}
                </p>
              )}
            </div>
          )}

          {/* URL Input */}
          {shouldShowInput('url') && (
            <div className={responsiveForm.field}>
              <Label htmlFor="inputUrl" className={responsiveForm.label}>
                {getInputLabel('url')}
              </Label>
              <Input
                id="inputUrl"
                type="url"
                value={formData.inputUrl}
                onChange={(e) => handleInputChange('inputUrl', e.target.value)}
                placeholder={
                  formData.agentType === 'web_scraping'
                    ? "https://example.com"
                    : "https://example.com/article-to-summarize"
                }
                className={cn(
                  responsiveForm.input,
                  validationErrors.inputUrl && 'border-red-500 focus:border-red-500'
                )}
                disabled={isSubmitting}
              />
              {validationErrors.inputUrl && (
                <p className="text-sm text-red-500 flex items-center gap-1 mt-1">
                  <AlertCircle className="h-3 w-3" />
                  {validationErrors.inputUrl}
                </p>
              )}
            </div>
          )}

          {/* Parameters */}
          <div className={responsiveForm.field}>
            <Label htmlFor="parameters" className={responsiveForm.label}>
              Advanced Parameters (Optional)
              <span className="text-sm text-muted-foreground font-normal ml-2">
                JSON format
              </span>
            </Label>
            <textarea
              id="parameters"
              value={formData.parameters}
              onChange={(e) => handleInputChange('parameters', e.target.value)}
              placeholder={getParametersPlaceholder(formData.agentType)}
              className={cn(
                "w-full min-h-[100px] px-4 py-3 text-base sm:min-h-[80px] sm:px-3 sm:py-2 sm:text-sm border border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-vertical font-mono rounded-md",
                validationErrors.parameters && 'border-red-500 focus:border-red-500'
              )}
              disabled={isSubmitting}
            />
            {validationErrors.parameters && (
              <p className="text-sm text-red-500 flex items-center gap-1 mt-1">
                <AlertCircle className="h-3 w-3" />
                {validationErrors.parameters}
              </p>
            )}
          </div>

          {/* Error Alert */}
          {error && (
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
            disabled={isSubmitting}
            className={cn("w-full touch-manipulation", responsiveForm.button)}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating Job...
              </>
            ) : (
              'Create Job'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
} 