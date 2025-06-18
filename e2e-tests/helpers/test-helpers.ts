import { Page, expect } from '@playwright/test';
import { selectors, timeouts, testUsers, TestUser, TestJobData, jobStatusProgression } from './test-data';

/**
 * Authentication helper functions
 */
export class AuthHelper {
  constructor(private page: Page) {}

  async login(user: TestUser = testUsers.admin): Promise<void> {
    await this.page.goto('/auth');
    
    // Wait for login form to be visible
    await this.page.waitForSelector(selectors.auth.loginForm, { timeout: timeouts.pageLoad });
    
    // Fill in credentials
    await this.page.fill(selectors.auth.emailInput, user.email);
    await this.page.fill(selectors.auth.passwordInput, user.password);
    
    // Submit login
    await this.page.click(selectors.auth.loginButton);
    
    // Wait for successful login (redirect to dashboard)
    await this.page.waitForURL('/', { timeout: timeouts.pageLoad });
    
    // Verify we're logged in by checking for logout button or user profile
    await expect(this.page.locator(selectors.auth.logoutButton)).toBeVisible({ timeout: timeouts.medium });
  }

  async logout(): Promise<void> {
    await this.page.click(selectors.auth.logoutButton);
    
    // Wait for redirect to login page
    await this.page.waitForURL('/auth', { timeout: timeouts.pageLoad });
    
    // Verify we're logged out
    await expect(this.page.locator(selectors.auth.loginForm)).toBeVisible();
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      await this.page.waitForSelector(selectors.auth.logoutButton, { timeout: timeouts.short });
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Job creation and management helper functions
 */
export class JobHelper {
  constructor(private page: Page) {}

  async createJob(jobData: TestJobData): Promise<string> {
    // Navigate to job creation form
    await this.page.goto('/schedule');
    
    // Wait for form to load
    await this.page.waitForSelector(selectors.jobForm.container, { timeout: timeouts.pageLoad });
    
    // Select agent from the agent selector (dropdown or similar UI)
    await this.page.click(selectors.jobForm.agentSelector);
    await this.page.click(`[data-testid="agent-option-${jobData.agent_identifier}"]`);
    
    // Wait for schema to load
    await this.page.waitForSelector(selectors.jobForm.titleInput, { timeout: timeouts.medium });
    
    // Check for any loading states or errors
    const loadingElement = this.page.locator(selectors.jobForm.loadingState);
    const errorElement = this.page.locator(selectors.jobForm.errorState);
    
    if (await loadingElement.isVisible()) {
      await loadingElement.waitFor({ state: 'hidden', timeout: timeouts.medium });
    }
    
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      throw new Error(`Failed to load agent schema: ${errorText}`);
    }
    
    // Fill in job title
    await this.page.fill(selectors.jobForm.titleInput, jobData.title);
    
    // Fill dynamic form fields based on the agent's schema
    await this.fillDynamicFields(jobData);
    
    // Submit the job
    await this.page.click(selectors.jobForm.submitButton);
    
    // Wait for successful submission and get job ID from the response or URL
    await this.page.waitForURL(/\/job\/[a-f0-9-]+/, { timeout: timeouts.pageLoad });
    
    // Extract job ID from URL
    const url = this.page.url();
    const jobId = url.match(/\/job\/([a-f0-9-]+)/)?.[1];
    
    if (!jobId) {
      throw new Error('Failed to extract job ID from URL');
    }
    
    return jobId;
  }

  private async fillDynamicFields(jobData: TestJobData): Promise<void> {
    // Iterate through the data fields and fill them dynamically
    for (const [fieldName, fieldValue] of Object.entries(jobData.data)) {
      const fieldSelector = selectors.jobForm.dynamicField(fieldName);
      
      try {
        // Check if field exists
        const fieldElement = this.page.locator(fieldSelector);
        
        if (await fieldElement.isVisible()) {
          if (typeof fieldValue === 'boolean') {
            // Handle checkbox fields
            if (fieldValue) {
              await fieldElement.check();
            } else {
              await fieldElement.uncheck();
            }
          } else if (typeof fieldValue === 'string' || typeof fieldValue === 'number') {
            // Handle text inputs and selects
            await fieldElement.fill(String(fieldValue));
          } else if (Array.isArray(fieldValue)) {
            // Handle array fields (convert to comma-separated string)
            await fieldElement.fill(fieldValue.join(', '));
          }
        }
      } catch (error) {
        console.warn(`Failed to fill field ${fieldName}:`, error);
        // Continue with other fields
      }
    }
  }

  async waitForJobCompletion(jobId: string, maxWaitTime: number = timeouts.jobCompletion): Promise<string> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      // Navigate to job details page
      await this.page.goto(`/job/${jobId}`);
      
      // Wait for page to load
      await this.page.waitForSelector(selectors.jobDetails.status, { timeout: timeouts.medium });
      
      // Get current status
      const statusElement = this.page.locator(selectors.jobDetails.status);
      const status = await statusElement.textContent();
      
      if (!status) {
        throw new Error('Could not read job status');
      }
      
      const normalizedStatus = status.toLowerCase().trim();
      
      // Check if job is complete
      if (normalizedStatus === 'completed' || normalizedStatus === 'failed') {
        return normalizedStatus;
      }
      
      // Wait before checking again
      await this.page.waitForTimeout(2000);
    }
    
    throw new Error(`Job ${jobId} did not complete within ${maxWaitTime}ms`);
  }

  async getJobDetails(jobId: string): Promise<any> {
    await this.page.goto(`/job/${jobId}`);
    await this.page.waitForSelector(selectors.jobDetails.container, { timeout: timeouts.pageLoad });
    
    // Extract job details from the page
    const title = await this.page.locator(selectors.jobDetails.title).textContent();
    const status = await this.page.locator(selectors.jobDetails.status).textContent();
    const agentIdentifier = await this.page.locator(selectors.jobDetails.agentIdentifier).textContent();
    
    // Try to get result if available
    let result = null;
    try {
      const resultElement = this.page.locator(selectors.jobDetails.result);
      if (await resultElement.isVisible()) {
        const resultText = await resultElement.textContent();
        if (resultText) {
          result = JSON.parse(resultText);
        }
      }
    } catch (error) {
      // Result might not be available or parseable
    }
    
    return {
      id: jobId,
      title: title?.trim(),
      status: status?.toLowerCase().trim(),
      agent_identifier: agentIdentifier?.trim(),
      result
    };
  }

  async deleteJob(jobId: string): Promise<void> {
    await this.page.goto(`/job/${jobId}`);
    await this.page.waitForSelector(selectors.jobDetails.deleteButton, { timeout: timeouts.medium });
    
    // Click delete button
    await this.page.click(selectors.jobDetails.deleteButton);
    
    // Handle confirmation dialog if it appears
    try {
      await this.page.waitForSelector(selectors.ui.confirmDialog, { timeout: timeouts.short });
      await this.page.click(selectors.ui.confirmButton);
    } catch {
      // No confirmation dialog, continue
    }
    
    // Wait for redirect back to job list
    await this.page.waitForURL('/', { timeout: timeouts.pageLoad });
  }

  async getJobList(): Promise<Array<{ title: string | null; status: string | null }>> {
    await this.page.goto('/');
    await this.page.waitForSelector(selectors.jobList.container, { timeout: timeouts.pageLoad });
    
    // Get all job items
    const jobElements = await this.page.locator(selectors.jobList.jobItem).all();
    
    const jobs: Array<{ title: string | null; status: string | null }> = [];
    for (const jobElement of jobElements) {
      const titleElement = jobElement.locator(selectors.jobList.jobTitle);
      const statusElement = jobElement.locator(selectors.jobList.jobStatus);
      
      const title = await titleElement.textContent();
      const status = await statusElement.textContent();
      
      jobs.push({
        title: title?.trim() || null,
        status: status?.toLowerCase().trim() || null
      });
    }
    
    return jobs;
  }

  async selectAgent(agentIdentifier: string): Promise<void> {
    // Click on agent selector
    await this.page.click(selectors.jobForm.agentSelector);
    
    // Wait for dropdown to open and select the agent
    await this.page.click(`[data-testid="agent-option-${agentIdentifier}"]`);
    
    // Wait for schema to load
    await this.page.waitForTimeout(1000);
  }
}

/**
 * Navigation helper functions
 */
export class NavigationHelper {
  constructor(private page: Page) {}

  async goToDashboard(): Promise<void> {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async goToJobCreation(): Promise<void> {
    await this.page.click(selectors.nav.newJob);
    await this.page.waitForSelector(selectors.jobForm.container);
  }

  async goToJobDetails(jobId: string): Promise<void> {
    await this.page.goto(`/job/${jobId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async refreshPage(): Promise<void> {
    await this.page.reload();
    await this.page.waitForLoadState('networkidle');
  }

  async goToNewJob(): Promise<void> {
    await this.goToJobCreation();
  }
}

/**
 * API helper functions for direct backend testing
 */
export class ApiHelper {
  constructor(private page: Page, private baseUrl: string = 'http://localhost:8000') {}

  async makeAuthenticatedRequest(method: string, endpoint: string, data?: any): Promise<any> {
    // Get auth token from page context/cookies
    const cookies = await this.page.context().cookies();
    const authToken = cookies.find(cookie => cookie.name === 'access_token')?.value;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await this.page.request.fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers,
      data: data ? JSON.stringify(data) : undefined
    });
    
    if (!response.ok()) {
      throw new Error(`API request failed: ${response.status()} ${response.statusText()}`);
    }
    
    return response.json();
  }

  async getJob(jobId: string): Promise<any> {
    return this.makeAuthenticatedRequest('GET', `/jobs/${jobId}`);
  }

  async deleteJob(jobId: string): Promise<void> {
    await this.makeAuthenticatedRequest('DELETE', `/jobs/${jobId}`);
  }

  async getJobs(): Promise<any[]> {
    const response = await this.makeAuthenticatedRequest('GET', '/jobs');
    return response.jobs || [];
  }

  async getAvailableAgents(): Promise<any[]> {
    const response = await this.makeAuthenticatedRequest('GET', '/agents');
    return response.agents || [];
  }
}

/**
 * Assertion helper functions
 */
export class AssertionHelper {
  constructor(private page: Page) {}

  async expectJobStatusProgression(jobId: string, maxWaitTime: number = timeouts.jobCompletion): Promise<void> {
    const seenStatuses: string[] = [];
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      await this.page.goto(`/job/${jobId}`);
      await this.page.waitForSelector(selectors.jobDetails.status, { timeout: timeouts.medium });
      
      const statusElement = this.page.locator(selectors.jobDetails.status);
      const status = await statusElement.textContent();
      
      if (status) {
        const normalizedStatus = status.toLowerCase().trim();
        
        if (!seenStatuses.includes(normalizedStatus)) {
          seenStatuses.push(normalizedStatus);
        }
        
        if (normalizedStatus === 'completed' || normalizedStatus === 'failed') {
          break;
        }
      }
      
      await this.page.waitForTimeout(2000);
    }
    
    // Verify the status progression makes sense
    for (let i = 0; i < seenStatuses.length - 1; i++) {
      const currentStatus = seenStatuses[i];
      const nextStatus = seenStatuses[i + 1];
      
      const currentIndex = jobStatusProgression.indexOf(currentStatus);
      const nextIndex = jobStatusProgression.indexOf(nextStatus);
      
      if (currentIndex >= 0 && nextIndex >= 0 && nextIndex < currentIndex) {
        throw new Error(`Invalid status progression: ${currentStatus} -> ${nextStatus}`);
      }
    }
  }

  async expectElementContainsText(selector: string, expectedText: string): Promise<void> {
    const element = this.page.locator(selector);
    await expect(element).toContainText(expectedText);
  }

  async expectElementVisible(selector: string): Promise<void> {
    const element = this.page.locator(selector);
    await expect(element).toBeVisible();
  }

  async expectElementNotVisible(selector: string): Promise<void> {
    const element = this.page.locator(selector);
    await expect(element).not.toBeVisible();
  }
} 