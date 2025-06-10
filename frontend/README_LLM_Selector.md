# LLM Selector Component Guide

The LLM Selector component provides dropdown controls for selecting LLM providers and their specific models. It dynamically fetches available providers and models from individual provider endpoints and automatically handles provider-specific model filtering.

**The LLM Selector is automatically integrated into job creation forms for agents that explicitly declare LLM provider fields using `form_field_type: "llm_provider"`.**

## Features

- **Dynamic Provider Loading**: Fetches available providers from the backend
- **Model Filtering**: Automatically updates model options based on selected provider
- **Status Indicators**: Shows provider availability and health status
- **Default Fallbacks**: Automatically selects default providers and models
- **Responsive Design**: Works on different screen sizes
- **Error Handling**: Graceful handling of API failures
- **Explicit Integration**: Only activates when agents explicitly declare LLM provider fields
- **No False Positives**: No confusion with regular fields named "provider" or "model"

## Explicit Integration

The LLM selector only appears when an agent explicitly declares a field with `form_field_type: "llm_provider"`. This ensures:
- No confusion with non-LLM fields named "provider" or "model" 
- Clear intent from the agent developer
- No false positives or misrendered fields
- Easy to understand and maintain

### How to Enable LLM Selection in Your Agent

To add LLM provider selection to your agent, use the explicit form field type:

```python
from pydantic import BaseModel, Field
from typing import Optional

@job_model
class MyAgentJobData(BaseModel):
    """Job data model with LLM provider selection"""
    
    # Regular fields
    prompt: str = Field(..., description="Text prompt to process")
    
    # LLM Provider field - this triggers the LLM selector
    provider: Optional[str] = Field(
        default=None, 
        description="LLM provider to use",
        json_schema_extra={"form_field_type": "llm_provider"}
    )
    
    # Model field - automatically handled when provider field exists
    model: Optional[str] = Field(
        default=None, 
        description="Specific model to use"
    )
    
    # Other LLM settings
    temperature: float = Field(default=0.7, description="Response temperature")
```

### Detection Logic

The system looks for fields with:
- `form_field_type: "llm_provider"` in the JSON schema
- When found, it renders the LLM selector for that field
- Automatically includes the corresponding `model` field in the selector
- Skips rendering the `model` field as a separate input

### Compatible Agents

Any agent can enable LLM selection by declaring a provider field with `form_field_type: "llm_provider"`:

- **Simple Prompt Agent** (`simple_prompt`) - ✅ Already enabled
- **Custom Agents** - Add the explicit form field type to enable

### How to Use in Job Forms

1. **Navigate to Job Creation**: Go to the job creation page and select a compatible agent
2. **Automatic Detection**: The system detects the explicit `llm_provider` form field type
3. **LLM Selection Interface**: You'll see the unified LLM Provider and Model dropdowns
4. **Select Provider**: Choose from available providers (Google AI, OpenAI, Anthropic, etc.)
5. **Select Model**: Choose from provider-specific models (automatically filtered)
6. **Configure Other Settings**: Set other agent-specific parameters

## Manual Usage (Standalone Component)

You can also use the LLMSelector component directly in your own forms:

```tsx
function MyComponent() {
  const [selectedProvider, setSelectedProvider] = useState<string>();
  const [selectedModel, setSelectedModel] = useState<string>();

  return (
    <LLMSelector
      selectedProvider={selectedProvider}
      selectedModel={selectedModel}
      onProviderChange={setSelectedProvider}
      onModelChange={setSelectedModel}
    />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `selectedProvider` | `string?` | `undefined` | Currently selected provider |
| `selectedModel` | `string?` | `undefined` | Currently selected model |
| `onProviderChange` | `(provider: string) => void` | - | Callback when provider changes |
| `onModelChange` | `(model: string) => void` | - | Callback when model changes |
| `className` | `string?` | `undefined` | Additional CSS classes |
| `disabled` | `boolean` | `false` | Disable both dropdowns |
| `showLabels` | `boolean` | `true` | Show field labels |
| `size` | `'sm' \| 'default'` | `'default'` | Control size |

## Integration Examples

### 1. Simple Form Integration

```tsx
import React, { useState } from 'react';
import { LLMSelector } from '@/components/LLMSelector';
import { Button } from '@/components/ui/button';

function PromptForm() {
  const [provider, setProvider] = useState<string>();
  const [model, setModel] = useState<string>();
  const [prompt, setPrompt] = useState('');

  const handleSubmit = async () => {
    const response = await fetch('/simple-prompt/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        provider,
        model
      })
    });
    // Handle response...
  };

  return (
    <form onSubmit={handleSubmit}>
      <LLMSelector
        selectedProvider={provider}
        selectedModel={model}
        onProviderChange={setProvider}
        onModelChange={setModel}
      />
      
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter your prompt..."
      />
      
      <Button type="submit">Submit</Button>
    </form>
  );
}
```

### 2. Compact Version

```tsx
<LLMSelector
  selectedProvider={provider}
  selectedModel={model}
  onProviderChange={setProvider}
  onModelChange={setModel}
  size="sm"
  showLabels={false}
  className="grid grid-cols-2 gap-2"
/>
```

### 3. With Form Libraries (React Hook Form)

```tsx
import { useForm, Controller } from 'react-hook-form';

function EnhancedForm() {
  const { control, handleSubmit } = useForm();

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name="provider"
        control={control}
        render={({ field }) => (
          <LLMSelector
            selectedProvider={field.value}
            selectedModel={modelValue}
            onProviderChange={field.onChange}
            onModelChange={setModelValue}
          />
        )}
      />
    </form>
  );
}
```

## Available Providers

The component automatically detects these providers:

- **Google AI** (🔍) - Gemini models
- **OpenAI** (🤖) - GPT models  
- **Anthropic** (🧠) - Claude models
- **Grok** (🚀) - xAI models
- **DeepSeek** (🔬) - DeepSeek models
- **Meta Llama** (🦙) - Llama models

## Provider Status Indicators

- **🟢 Available**: Provider is loaded and ready
- **🔴 Unavailable**: Provider failed to load
- **🟡 Unknown**: Provider status unclear

## API Integration

The component connects to individual provider endpoints to gather information:

- `GET /google-ai/models` - Google AI provider models
- `GET /openai/models` - OpenAI provider models  
- `GET /anthropic/models` - Anthropic provider models
- `GET /grok/models` - Grok provider models
- `GET /deepseek/models` - DeepSeek provider models
- `GET /llama/models` - Meta Llama provider models

The component aggregates this data locally to provide a unified interface for provider and model selection.

## Job Form Integration Details

The LLM Selector is automatically integrated into the JobForm component when it detects LLM provider fields with the explicit form field type. Here's how it works:

1. **Explicit Field Detection**: The JobForm looks for fields with `form_field_type: "llm_provider"`
2. **Component Replacement**: The standard `provider` input field is replaced with the LLMSelector component  
3. **Automatic Model Inclusion**: The `model` field is automatically included in the selector interface
4. **Form Validation**: Integrated with the form's validation system
5. **Error Handling**: Provider and model selection errors are displayed inline
6. **Data Submission**: Selected provider and model are included in the job data automatically

### Technical Implementation

The integration works by:

- **Explicit Detection**: Checking for `form_field_type: "llm_provider"` in the schema
- **Component Replacement**: Replacing the provider field with the combined LLMSelector 
- **Model Field Skipping**: Automatically skipping the model field since it's handled by the selector
- **State Management**: Handling form state for both fields together through the unified component
- **Validation Integration**: Connecting validation errors for both provider and model fields

## Styling

The component uses Tailwind CSS classes and follows the shadcn/ui design system. You can customize appearance with:

```tsx
<LLMSelector
  className="max-w-md"
  // Custom styling
/>
```

## Error Handling

The component handles these error scenarios:

1. **API Unavailable**: Shows error message with retry option
2. **No Providers**: Disables dropdowns with helpful message
3. **Provider Change**: Automatically switches to compatible models
4. **Form Validation**: Integrates with job form validation system

## TypeScript Support

Full TypeScript support with proper type definitions:

```tsx
interface LLMProvider {
  provider: string;
  status: string;
  service_name: string;
  default_model: string;
  available_models: string[];
}

interface ProvidersInfo {
  default_provider: string;
  available_providers: string[];
  providers: Record<string, LLMProvider>;
}
```

## Best Practices

1. **Always handle loading states** - The component shows loading indicators
2. **Implement error boundaries** - Wrap in error boundary for production
3. **Cache provider data** - Consider caching for better performance
4. **Test fallbacks** - Ensure graceful degradation when providers are unavailable
5. **Monitor health** - Use health endpoints to track provider status

## Troubleshooting

**Component not loading providers?**
- Check if Simple Prompt Agent is running
- Verify API base URL configuration
- Check authentication token

**Models not updating when provider changes?**
- Ensure both callback functions are provided
- Check for JavaScript errors in console
- Verify provider has available models

**LLM Selector not appearing in job form?**
- Verify the agent has a field with `form_field_type: "llm_provider"` in its schema
- Check that the backend is correctly preserving the explicit form field type
- Ensure the agent schema is loading correctly
- Confirm the field is declared using `json_schema_extra={"form_field_type": "llm_provider"}`

**Need to add LLM support to a custom agent?**
- Add a provider field with `json_schema_extra={"form_field_type": "llm_provider"}`
- Add a corresponding `model` field (will be automatically included in the selector)
- Use enum values with known provider names for better UX
- Test the schema endpoint to verify the form field type is present

**Styling issues?**
- Ensure Tailwind CSS is configured
- Check if shadcn/ui components are installed
- Verify CSS classes are not being overridden 