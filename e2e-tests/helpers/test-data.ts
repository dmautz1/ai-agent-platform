/**
 * Test data and utilities for E2E testing
 */

export interface TestUser {
  email: string;
  password: string;
  name?: string;
}

export interface TestJobData {
  agentType: 'text_processing' | 'summarization' | 'web_scraping';
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

// Test job data for different agent types
export const testJobs: Record<string, TestJobData> = {
  textProcessing: {
    agentType: 'text_processing',
    title: 'E2E Test Text Processing',
    data: {
      input_text: 'This is a test text for sentiment analysis. I am very happy with this service!',
      operation: 'sentiment_analysis',
      language: 'en'
    }
  },
  
  summarization: {
    agentType: 'summarization',
    title: 'E2E Test Summarization',
    data: {
      input_text: 'This is a long text that needs to be summarized. It contains multiple sentences with various topics. The goal is to create a concise summary that captures the main points of the original text. This will help users quickly understand the key information without reading the entire document.',
      max_summary_length: 100,
      format: 'paragraph'
    }
  },
  
  webScraping: {
    agentType: 'web_scraping',
    title: 'E2E Test Web Scraping',
    data: {
      input_url: 'https://httpbin.org/html',
      max_pages: 1,
      extract_metadata: true,
      selectors: ['h1', 'p']
    }
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
    info: (type: string) => `/agents/${type}`,
    test: (type: string) => `/agents/${type}/test`
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
  
  // Job Creation Form
  jobForm: {
    container: '[data-testid="job-form"]',
    agentTypeSelect: '[data-testid="agent-type-select"]',
    titleInput: '[data-testid="job-title-input"]',
    submitButton: '[data-testid="submit-job-button"]',
    
    // Text Processing fields
    textProcessing: {
      inputText: '[data-testid="input-text"]',
      operation: '[data-testid="operation-select"]',
      language: '[data-testid="language-select"]'
    },
    
    // Summarization fields
    summarization: {
      inputText: '[data-testid="input-text"]',
      inputUrl: '[data-testid="input-url"]',
      maxLength: '[data-testid="max-summary-length"]',
      format: '[data-testid="format-select"]'
    },
    
    // Web Scraping fields
    webScraping: {
      inputUrl: '[data-testid="input-url"]',
      maxPages: '[data-testid="max-pages"]',
      selectors: '[data-testid="selectors-input"]',
      extractMetadata: '[data-testid="extract-metadata-checkbox"]'
    }
  },
  
  // Job List
  jobList: {
    container: '[data-testid="job-list"]',
    jobItem: '[data-testid^="job-item-"]',
    jobTitle: '[data-testid^="job-title-"]',
    jobStatus: '[data-testid^="job-status-"]',
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
    agentType: '[data-testid="job-agent-type"]',
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

// Helper to generate unique test data
export function generateTestData(baseName: string): { 
  email: string; 
  title: string; 
  timestamp: string;
} {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    email: `${baseName}-${timestamp}@test.com`,
    title: `${baseName} ${timestamp}`,
    timestamp
  };
}

// Helper to create expected job result structure based on agent type
export function getExpectedJobResultStructure(agentType: string): Record<string, string> {
  switch (agentType) {
    case 'text_processing':
      return {
        type: 'text_processing',
        processed_text: 'string',
        'analysis.sentiment.score': 'number',
        'analysis.sentiment.label': 'string',
        'analysis.sentiment.confidence': 'number'
      };
      
    case 'summarization':
      return {
        type: 'summarization',
        summary: 'string',
        original_length: 'number',
        summary_length: 'number',
        compression_ratio: 'number'
      };
      
    case 'web_scraping':
      return {
        type: 'web_scraping',
        'scraped_data.url': 'string',
        'scraped_data.content': 'string',
        pages_processed: 'number',
        success_rate: 'number'
      };
      
    default:
      return {};
  }
}

// Helper to validate job result structure
export function isValidJobResult(result: any, agentType: string): boolean {
  const expectedStructure = getExpectedJobResultStructure(agentType);
  
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