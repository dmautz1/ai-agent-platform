import { test, expect } from '@playwright/test';
import { AuthHelper, JobHelper, NavigationHelper, AssertionHelper, ApiHelper } from './helpers/test-helpers';
import { testUsers, testJobs, selectors, timeouts, generateTestData, isValidJobResult } from './helpers/test-data';

test.describe('Complete Job Workflow', () => {
  let authHelper: AuthHelper;
  let jobHelper: JobHelper;
  let navHelper: NavigationHelper;
  let assertionHelper: AssertionHelper;
  let apiHelper: ApiHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    jobHelper = new JobHelper(page);
    navHelper = new NavigationHelper(page);
    assertionHelper = new AssertionHelper(page);
    apiHelper = new ApiHelper(page);
    
    // Login before each test
    await authHelper.login(testUsers.admin);
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: logout after each test
    await authHelper.logout();
  });

  test.describe('Generic Agent Workflow', () => {
    test('should complete full simple prompt agent job workflow', async ({ page }) => {
      const testData = generateTestData('simple-prompt');
      const jobData = {
        ...testJobs.simple_prompt,
        title: testData.title
      };

      // Step 1: Create job
      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Step 2: Verify job appears in details page
      const jobDetails = await jobHelper.getJobDetails(jobId);
      expect(jobDetails.title).toBe(jobData.title);
      expect(jobDetails.agent_identifier).toBe('simple_prompt');

      // Step 3: Wait for job completion and monitor status progression
      await assertionHelper.expectJobStatusProgression(jobId);
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Step 4: Verify job result structure
      const completedJobDetails = await jobHelper.getJobDetails(jobId);
      expect(completedJobDetails.result).toBeTruthy();
      expect(isValidJobResult(completedJobDetails.result, 'simple_prompt')).toBe(true);

      // Step 5: Verify job appears in job list
      const jobList = await jobHelper.getJobList();
      const listJob = jobList.find(job => job.title === jobData.title);
      expect(listJob).toBeTruthy();
      expect(listJob?.status).toBe('completed');

      // Step 6: Test job deletion
      await jobHelper.deleteJob(jobId);
      
      // Verify job is removed from list
      const updatedJobList = await jobHelper.getJobList();
      const deletedJob = updatedJobList.find(job => job.title === jobData.title);
      expect(deletedJob).toBeFalsy();
    });
  });

  test.describe('Complex Prompt Workflow', () => {
    test('should complete full complex prompt job workflow', async ({ page }) => {
      const testData = generateTestData('complex-prompt');
      const jobData = {
        ...testJobs.complex_prompt,
        title: testData.title
      };

      // Create and process complex prompt job
      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Wait for completion
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Verify result structure
      const jobDetails = await jobHelper.getJobDetails(jobId);
      expect(jobDetails.result).toBeTruthy();
      expect(isValidJobResult(jobDetails.result, 'simple_prompt')).toBe(true);

      // Cleanup
      await jobHelper.deleteJob(jobId);
    });
  });

  test.describe('Agent Discovery Integration', () => {
    test('should dynamically discover available agents and create jobs', async ({ page }) => {
      // Get available agents from the discovery system
      const availableAgents = await apiHelper.getAvailableAgents();
      expect(availableAgents.length).toBeGreaterThan(0);
      
      // Find the simple_prompt agent
      const simplePromptAgent = availableAgents.find(agent => agent.identifier === 'simple_prompt');
      expect(simplePromptAgent).toBeTruthy();
      expect(simplePromptAgent?.enabled).toBe(true);

      // Create job using discovered agent
      const testData = generateTestData('discovery-test');
      const jobData = {
        agent_identifier: simplePromptAgent!.identifier,
        title: testData.title,
        data: testData.data
      };

      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Wait for completion
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Cleanup
      await jobHelper.deleteJob(jobId);
    });
  });

  test.describe('Job Management Features', () => {
    test('should handle multiple concurrent jobs', async ({ page }) => {
      const jobIds: string[] = [];
      
      try {
        // Create multiple jobs using the same agent type
        const jobs = [
          { ...testJobs.simple_prompt, title: generateTestData('concurrent-1').title },
          { ...testJobs.complex_prompt, title: generateTestData('concurrent-2').title }
        ];

        // Create all jobs
        for (const jobData of jobs) {
          const jobId = await jobHelper.createJob(jobData);
          jobIds.push(jobId);
        }

        // Wait for all jobs to complete
        const completionPromises = jobIds.map(jobId => 
          jobHelper.waitForJobCompletion(jobId)
        );
        
        const results = await Promise.all(completionPromises);
        
        // Verify all jobs completed successfully
        results.forEach(status => {
          expect(status).toBe('completed');
        });

      } finally {
        // Cleanup all created jobs
        for (const jobId of jobIds) {
          try {
            await jobHelper.deleteJob(jobId);
          } catch (error) {
            console.warn(`Failed to cleanup job ${jobId}:`, error);
          }
        }
      }
    });

    test('should refresh job list and show real-time updates', async ({ page }) => {
      const testData = generateTestData('refresh-test');
      const jobData = {
        ...testJobs.simple_prompt,
        title: testData.title
      };

      try {
        // Create job
        const jobId = await jobHelper.createJob(jobData);
        
        // Navigate to dashboard
        await navHelper.goToDashboard();
        
        // Verify job appears in list
        let jobList = await jobHelper.getJobList();
        let listJob = jobList.find(job => job.title === jobData.title);
        expect(listJob).toBeTruthy();
        
        // Wait for job completion
        await jobHelper.waitForJobCompletion(jobId);
        
        // Refresh page and verify updated status
        await navHelper.refreshPage();
        
        jobList = await jobHelper.getJobList();
        listJob = jobList.find(job => job.title === jobData.title);
        expect(listJob?.status).toBe('completed');
        
        // Cleanup
        await jobHelper.deleteJob(jobId);
        
      } catch (error) {
        console.error('Test failed:', error);
        throw error;
      }
    });
  });

  test.describe('Dynamic Form Generation', () => {
    test('should dynamically generate form based on agent schema', async ({ page }) => {
      // Navigate to job creation
      await navHelper.goToNewJob();
      
      // Select agent and verify dynamic form generation
      await jobHelper.selectAgent('simple_prompt');
      
      // Wait for schema to load and form to render
      await page.waitForSelector(selectors.jobForm.dynamicField('prompt'));
      
      // Verify expected fields exist based on simple_prompt agent schema
      const promptField = page.locator(selectors.jobForm.dynamicField('prompt'));
      const maxTokensField = page.locator(selectors.jobForm.dynamicField('max_tokens'));
      
      await expect(promptField).toBeVisible();
      await expect(maxTokensField).toBeVisible();
      
      // Fill the dynamic form
      await promptField.fill('Test prompt for dynamic form');
      await maxTokensField.fill('100');
      
      // Submit job
      await page.locator(selectors.jobForm.titleInput).fill('Dynamic Form Test');
      await page.locator(selectors.jobForm.submitButton).click();
      
      // Verify job was created successfully
      await expect(page.locator(selectors.ui.successAlert)).toBeVisible();
    });
  });
}); 