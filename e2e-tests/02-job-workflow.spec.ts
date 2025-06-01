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

  test.describe('Text Processing Agent Workflow', () => {
    test('should complete full text processing job workflow', async ({ page }) => {
      const testData = generateTestData('text-processing');
      const jobData = {
        ...testJobs.textProcessing,
        title: testData.title
      };

      // Step 1: Create job
      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Step 2: Verify job appears in details page
      const jobDetails = await jobHelper.getJobDetails(jobId);
      expect(jobDetails.title).toBe(jobData.title);
      expect(jobDetails.agentType).toContain('text');

      // Step 3: Wait for job completion and monitor status progression
      await assertionHelper.expectJobStatusProgression(jobId);
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Step 4: Verify job result structure
      const completedJobDetails = await jobHelper.getJobDetails(jobId);
      expect(completedJobDetails.result).toBeTruthy();
      expect(isValidJobResult(completedJobDetails.result, 'text_processing')).toBe(true);

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

  test.describe('Summarization Agent Workflow', () => {
    test('should complete full summarization job workflow', async ({ page }) => {
      const testData = generateTestData('summarization');
      const jobData = {
        ...testJobs.summarization,
        title: testData.title
      };

      // Create and process summarization job
      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Wait for completion
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Verify result structure
      const jobDetails = await jobHelper.getJobDetails(jobId);
      expect(jobDetails.result).toBeTruthy();
      expect(isValidJobResult(jobDetails.result, 'summarization')).toBe(true);

      // Cleanup
      await jobHelper.deleteJob(jobId);
    });
  });

  test.describe('Web Scraping Agent Workflow', () => {
    test('should complete full web scraping job workflow', async ({ page }) => {
      const testData = generateTestData('web-scraping');
      const jobData = {
        ...testJobs.webScraping,
        title: testData.title
      };

      // Create and process web scraping job
      const jobId = await jobHelper.createJob(jobData);
      expect(jobId).toBeTruthy();

      // Wait for completion
      const finalStatus = await jobHelper.waitForJobCompletion(jobId);
      expect(finalStatus).toBe('completed');

      // Verify result structure
      const jobDetails = await jobHelper.getJobDetails(jobId);
      expect(jobDetails.result).toBeTruthy();
      expect(isValidJobResult(jobDetails.result, 'web_scraping')).toBe(true);

      // Cleanup
      await jobHelper.deleteJob(jobId);
    });
  });

  test.describe('Job Management Features', () => {
    test('should handle multiple concurrent jobs', async ({ page }) => {
      const jobIds: string[] = [];
      
      try {
        // Create multiple jobs of different types
        const jobs = [
          { ...testJobs.textProcessing, title: generateTestData('concurrent-1').title },
          { ...testJobs.summarization, title: generateTestData('concurrent-2').title }
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
        ...testJobs.textProcessing,
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
}); 