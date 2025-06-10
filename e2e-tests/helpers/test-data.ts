/**
 * Test data and utilities for E2E testing
 */

export interface TestUser {
  email: string;
  password: string;
  name?: string;
}

export interface TestJobData {
  agent_identifier: string;
  title: string;
  data: Record<string, any>;
}

// Test users for authentication testing
export const testUsers: Record<string, TestUser> = {
  admin: {
    email: 'admin@example.com',
    password: 'admin123!',
    name: 'Test Admin'
  },
  user: {
    email: 'user@example.com', 
    password: 'user123!',
    name: 'Test User'
  }
};

// Test jobs using the actual simple_example_agent
export const testJobs = {
  simple_prompt: {
    agent_identifier: 'simple_prompt',
    title: 'Simple Prompt Test',
    data: {
      prompt: 'Hello, how are you today?',
      max_tokens: 100
    },
    priority: 5,
    tags: ['test', 'prompt']
  },
  
  complex_prompt: {
    agent_identifier: 'simple_prompt', 
    title: 'Complex Prompt Test',
    data: {
      prompt: 'Explain quantum computing in simple terms that a beginner can understand.',
      max_tokens: 500
    },
    priority: 7,
    tags: ['test', 'complex', 'prompt']
  }
};

// API endpoints
export const apiEndpoints = {
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    me: '/auth/me'
  },
  jobs: {
    create: '/jobs',
    list: '/jobs',
    get: (id: string) => `/jobs/${id}`,
    delete: (id: string) => `/jobs/${id}`
  },
  agents: {
    list: '/agents',
    info: (identifier: string) => `/agents/${identifier}`,
    test: (identifier: string) => `/agents/${identifier}/test`,
    schema: (identifier: string) => `/agents/${identifier}/schema`
  }
};

// Common selectors used across tests
export const selectors = {
  // Navigation
  nav: {
    dashboard: '[data-testid="nav-dashboard"]',
    jobs: '[data-testid="nav-jobs"]',
    newJob: '[data-testid="nav-new-job"]',
    profile: '[data-testid="nav-profile"]'
  },
  
  // Authentication
  auth: {
    emailInput: '[data-testid="email-input"]',
    passwordInput: '[data-testid="password-input"]',
    loginButton: '[data-testid="login-button"]',
    logoutButton: '[data-testid="logout-button"]',
    loginForm: '[data-testid="login-form"]'
  },
  
  // Job Creation Form (Dynamic Agent Form)
  jobForm: {
    container: '[data-testid="job-form"]',
    agentSelector: '[data-testid="agent-selector"]',
    titleInput: '[data-testid="job-title-input"]',
    submitButton: '[data-testid="submit-job-button"]',
    loadingState: '[data-testid="loading-schema"]',
    errorState: '[data-testid="schema-error"]',
    
    // Dynamic form fields (will vary by agent)
    dynamicField: (fieldName: string) => `[data-testid="field-${fieldName}"]`,
    textInput: '[data-testid^="field-"][data-testid$="-input"]',
    select: '[data-testid^="field-"][data-testid$="-select"]',
    checkbox: '[data-testid^="field-"][data-testid$="-checkbox"]'
  },
  
  // Job List
  jobList: {
    container: '[data-testid="job-list"]',
    jobItem: '[data-testid^="job-item-"]',
    jobTitle: '[data-testid^="job-title-"]',
    jobStatus: '[data-testid^="job-status-"]',
    jobAgentId: '[data-testid^="job-agent-id-"]',
    jobActions: '[data-testid^="job-actions-"]',
    viewButton: '[data-testid^="view-job-"]',
    deleteButton: '[data-testid^="delete-job-"]',
    refreshButton: '[data-testid="refresh-jobs"]',
    emptyState: '[data-testid="empty-jobs"]'
  },
  
  // Job Details
  jobDetails: {
    container: '[data-testid="job-details"]',
    title: '[data-testid="job-title"]',
    status: '[data-testid="job-status"]',
    agentIdentifier: '[data-testid="job-agent-identifier"]',
    createdAt: '[data-testid="job-created-at"]',
    updatedAt: '[data-testid="job-updated-at"]',
    inputData: '[data-testid="job-input-data"]',
    result: '[data-testid="job-result"]',
    errorMessage: '[data-testid="job-error"]',
    deleteButton: '[data-testid="delete-job-button"]',
    backButton: '[data-testid="back-to-list"]'
  },
  
  // Common UI elements
  ui: {
    loadingSpinner: '[data-testid="loading-spinner"]',
    errorAlert: '[data-testid="error-alert"]',
    successAlert: '[data-testid="success-alert"]',
    confirmDialog: '[data-testid="confirm-dialog"]',
    confirmButton: '[data-testid="confirm-action"]',
    cancelButton: '[data-testid="cancel-action"]'
  }
};

// Wait timeouts
export const timeouts = {
  short: 2000,
  medium: 5000,
  long: 10000,
  jobCompletion: 30000, // Jobs might take time to complete
  pageLoad: 15000
};

// Expected job statuses in order
export const jobStatusProgression = [
  'pending',
  'running', 
  'completed' // or 'failed'
];

// Generate test data with unique identifiers
export const generateTestData = (suffix: string) => ({
  agent_identifier: 'simple_prompt',
  title: `Test Job ${suffix}`,
  data: {
    prompt: `This is a test prompt for ${suffix}`,
    max_tokens: 200
  },
  priority: Math.floor(Math.random() * 10) + 1,
  tags: ['test', 'auto-generated']
});

// Invalid job data for testing validation
export const invalidJobData = {
  no_agent: {
    title: 'Missing Agent',
    data: {
      prompt: 'Test prompt'
    }
  },
  
  invalid_agent: {
    agent_identifier: 'nonexistent_agent',
    title: 'Invalid Agent',
    data: {
      prompt: 'Test prompt'
    }
  },
  
  missing_data: {
    agent_identifier: 'simple_prompt',
    title: 'Missing Data'
  },
  
  invalid_data: {
    agent_identifier: 'simple_prompt', 
    title: 'Invalid Data',
    data: {
      // Missing required prompt field
      max_tokens: 100
    }
  }
};

// Helper to create expected job result structure based on agent identifier
export function getExpectedJobResultStructure(agentIdentifier: string): Record<string, string> {
  // Map agent identifiers to expected result structures
  switch (agentIdentifier) {
    case 'example_research_agent':
      return {
        agent_identifier: 'string',
        results: 'object',
        'results.0.title': 'string',
        'results.0.content': 'string',
        total_results: 'number',
        processing_time_ms: 'number'
      };
      
    case 'content_summarizer':
      return {
        agent_identifier: 'string',
        summary: 'string',
        original_length: 'number',
        summary_length: 'number',
        compression_ratio: 'number',
        processing_time_ms: 'number'
      };
      
    case 'web_data_extractor':
      return {
        agent_identifier: 'string',
        'extracted_data.url': 'string',
        'extracted_data.content': 'string',
        pages_processed: 'number',
        success_rate: 'number',
        processing_time_ms: 'number'
      };
      
    default:
      // Generic structure for unknown agents
      return {
        agent_identifier: 'string',
        processing_time_ms: 'number'
      };
  }
}

// Helper to validate job result structure
export function isValidJobResult(result: any, agentIdentifier: string): boolean {
  const expectedStructure = getExpectedJobResultStructure(agentIdentifier);
  
  for (const [path, expectedType] of Object.entries(expectedStructure)) {
    const value = getNestedValue(result, path);
    
    if (value === undefined) {
      return false;
    }
    
    if (typeof value !== expectedType) {
      return false;
    }
  }
  
  return true;
}

// Helper to get nested object value by path
function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj);
} 