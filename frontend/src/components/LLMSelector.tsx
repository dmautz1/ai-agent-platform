import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, Zap, Cpu } from 'lucide-react';
import { handleApiError } from '@/lib/api';
import { cn } from '@/lib/utils';
import axios from 'axios';

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

interface LLMSelectorProps {
  selectedProvider?: string;
  selectedModel?: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  className?: string;
  disabled?: boolean;
  showLabels?: boolean;
  size?: 'sm' | 'default';
}

// Create a simple API client for LLM endpoints
const createApiClient = () => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add auth token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    client.defaults.headers.Authorization = `Bearer ${token}`;
  }

  return client;
};

export function LLMSelector({
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  className,
  disabled = false,
  showLabels = true,
  size = 'default'
}: LLMSelectorProps) {
  const [providersInfo, setProvidersInfo] = useState<ProvidersInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch providers information from individual provider endpoints
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const apiClient = createApiClient();
        const providerNames = ['google-ai', 'openai', 'anthropic', 'grok', 'deepseek', 'llama'];
        const providers: Record<string, LLMProvider> = {};
        const availableProviders: string[] = [];
        
        // Fetch data from each provider endpoint
        for (const providerName of providerNames) {
          try {
            const response = await apiClient.get(`/${providerName}/models`);
            if (response.data.success && response.data.result && response.data.result.models) {
              // Map endpoint names to internal provider names
              const internalName = providerName === 'google-ai' ? 'google' : providerName;
              const providerData = response.data.result;
              
              providers[internalName] = {
                provider: internalName,
                status: 'available',
                service_name: getServiceDisplayName(providerName),
                default_model: providerData.models && providerData.models[0] ? providerData.models[0] : '',
                available_models: providerData.models || []
              };
              availableProviders.push(internalName);
            }
          } catch (err) {
            // Provider failed to load - mark as unavailable
            const internalName = providerName === 'google-ai' ? 'google' : providerName;
            providers[internalName] = {
              provider: internalName,
              status: 'failed',
              service_name: getServiceDisplayName(providerName),
              default_model: '',
              available_models: []
            };
            console.warn(`Provider ${providerName} failed to load:`, err);
          }
        }
        
        const providersData: ProvidersInfo = {
          default_provider: availableProviders.includes('google') ? 'google' : availableProviders[0] || 'google',
          available_providers: availableProviders,
          providers
        };
        
        setProvidersInfo(providersData);
        
      } catch (err) {
        const errorMessage = handleApiError(err);
        setError(errorMessage);
        console.error('Failed to fetch LLM providers:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProviders();
  }, []); // Empty dependency array - only run once on mount

  // Set default provider when providers are loaded and no provider is selected
  useEffect(() => {
    if (providersInfo && !selectedProvider && providersInfo.default_provider) {
      onProviderChange(providersInfo.default_provider);
    }
  }, [providersInfo, selectedProvider, onProviderChange]);

  // Helper function to get display names for services
  const getServiceDisplayName = (providerName: string) => {
    switch (providerName) {
      case 'google-ai':
        return 'Google AI';
      case 'openai':
        return 'OpenAI';
      case 'anthropic':
        return 'Anthropic';
      case 'grok':
        return 'Grok (xAI)';
      case 'deepseek':
        return 'DeepSeek';
      case 'llama':
        return 'Meta Llama';
      default:
        return providerName;
    }
  };

  // Update model when provider changes
  useEffect(() => {
    if (selectedProvider && providersInfo?.providers[selectedProvider]) {
      const provider = providersInfo.providers[selectedProvider];
      const currentModel = selectedModel;
      
      // If current model is not available in the new provider, use default
      if (!currentModel || !provider.available_models.includes(currentModel)) {
        onModelChange(provider.default_model);
      }
    }
  }, [selectedProvider, providersInfo, selectedModel, onModelChange]);

  const getProviderIcon = (providerName: string) => {
    switch (providerName.toLowerCase()) {
      case 'openai':
        return '🤖';
      case 'google':
        return '🔍';
      case 'anthropic':
        return '🧠';
      case 'grok':
        return '🚀';
      case 'deepseek':
        return '🔬';
      case 'llama':
        return '🦙';
      default:
        return '⚡';
    }
  };

  const getProviderStatus = (provider: LLMProvider) => {
    if (provider.status === 'available') {
      return { color: 'text-green-600', label: 'Available' };
    } else if (provider.status === 'failed') {
      return { color: 'text-red-600', label: 'Unavailable' };
    } else {
      return { color: 'text-yellow-600', label: 'Unknown' };
    }
  };

  if (loading) {
    return (
      <div className={cn("space-y-4", className)}>
        {showLabels && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">LLM Provider</Label>
            <div className="flex items-center space-x-2 p-3 border rounded-md">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Loading providers...</span>
            </div>
          </div>
        )}
        
        {showLabels && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Model</Label>
            <div className="flex items-center space-x-2 p-3 border rounded-md">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Loading models...</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("space-y-4", className)}>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load LLM providers: {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!providersInfo) {
    return null;
  }

  const availableProviders = providersInfo.available_providers || [];
  const selectedProviderInfo = selectedProvider ? providersInfo.providers[selectedProvider] : null;
  const availableModels = selectedProviderInfo?.available_models || [];

  return (
    <div className={cn("space-y-4", className)}>
      {/* Provider Selection */}
      <div className="space-y-2">
        {showLabels && (
          <Label htmlFor="llm-provider" className="text-sm font-medium flex items-center gap-2">
            <Zap className="h-4 w-4" />
            LLM Provider
          </Label>
        )}
        <Select
          value={selectedProvider || ''}
          onValueChange={onProviderChange}
          disabled={disabled || availableProviders.length === 0}
        >
          <SelectTrigger 
            id="llm-provider"
            className={cn("w-full", size === 'sm' && "h-8")}
          >
            <SelectValue placeholder="Select a provider">
              {selectedProvider && (
                <div className="flex items-center gap-2">
                  <span>{getProviderIcon(selectedProvider)}</span>
                  <span>{providersInfo.providers[selectedProvider]?.service_name || selectedProvider}</span>
                  {selectedProviderInfo && (
                    <span className={cn("text-xs", getProviderStatus(selectedProviderInfo).color)}>
                      •
                    </span>
                  )}
                </div>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availableProviders.map((providerKey) => {
              const provider = providersInfo.providers[providerKey];
              if (!provider) return null;
              
              const status = getProviderStatus(provider);
              const isDefault = providerKey === providersInfo.default_provider;
              
              return (
                <SelectItem 
                  key={providerKey} 
                  value={providerKey}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <span>{getProviderIcon(providerKey)}</span>
                    <div className="flex flex-col">
                      <span className="text-sm">{provider.service_name}</span>
                      <div className="flex items-center gap-2">
                        <span className={cn("text-xs", status.color)}>
                          {status.label}
                        </span>
                        {isDefault && (
                          <span className="text-xs text-blue-600 font-medium">Default</span>
                        )}
                      </div>
                    </div>
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {/* Model Selection */}
      <div className="space-y-2">
        {showLabels && (
          <Label htmlFor="llm-model" className="text-sm font-medium flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            Model
          </Label>
        )}
        <Select
          value={selectedModel || ''}
          onValueChange={onModelChange}
          disabled={disabled || !selectedProvider || availableModels.length === 0}
        >
          <SelectTrigger 
            id="llm-model"
            className={cn("w-full", size === 'sm' && "h-8")}
          >
            <SelectValue placeholder="Select a model">
              {selectedModel && (
                <div className="flex items-center gap-2">
                  <span className="text-sm">{selectedModel}</span>
                  {selectedModel === selectedProviderInfo?.default_model && (
                    <span className="text-xs text-blue-600">Default</span>
                  )}
                </div>
              )}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {availableModels.map((model) => {
              const isDefault = model === selectedProviderInfo?.default_model;
              
              return (
                <SelectItem key={model} value={model}>
                  <div className="flex items-center justify-between w-full">
                    <span className="text-sm">{model}</span>
                    {isDefault && (
                      <span className="text-xs text-blue-600 font-medium ml-2">Default</span>
                    )}
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {/* Info Display */}
      {selectedProviderInfo && (
        <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded-md">
          <div className="flex items-center justify-between">
            <span>
              Models: {selectedProviderInfo.available_models.length}
            </span>
            <span className={cn(getProviderStatus(selectedProviderInfo).color)}>
              {getProviderStatus(selectedProviderInfo).label}
            </span>
          </div>
        </div>
      )}
    </div>
  );
} 