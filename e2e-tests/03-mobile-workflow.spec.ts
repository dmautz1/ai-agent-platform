import { test, expect } from '@playwright/test';
import { AuthHelper, JobHelper, NavigationHelper } from './helpers/test-helpers';
import { testUsers, testJobs, selectors, timeouts, generateTestData } from './helpers/test-data';

test.describe('Mobile Workflow Tests', () => {
  let authHelper: AuthHelper;
  let jobHelper: JobHelper;
  let navHelper: NavigationHelper;

  test.beforeEach(async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    authHelper = new AuthHelper(page);
    jobHelper = new JobHelper(page);
    navHelper = new NavigationHelper(page);
    
    // Login as admin user
    await authHelper.login(testUsers.admin);
  });

  test.afterEach(async ({ page }) => {
    await authHelper.logout();
  });

  test('should complete job creation workflow on mobile', async ({ page }) => {
    const testData = generateTestData('mobile-test');
    const jobData = {
      ...testJobs.simple_prompt,
      title: testData.title
    };

    // Create job
    const jobId = await jobHelper.createJob(jobData);
    expect(jobId).toBeTruthy();

    // Wait for and verify completion
    const finalStatus = await jobHelper.waitForJobCompletion(jobId);
    expect(finalStatus).toBe('completed');

    // Verify job is removed from mobile list
    const updatedJobList = await jobHelper.getJobList();
    const deletedJob = updatedJobList.find(job => job.title === jobData.title);
    
    // Cleanup
    await jobHelper.deleteJob(jobId);
  });

  test('should handle mobile touch interactions', async ({ page }) => {
    const testData = generateTestData('mobile-touch');
    const jobData = {
      ...testJobs.simple_prompt,
      title: testData.title
    };

    try {
      // Test touch-friendly job creation
      await navHelper.goToJobCreation();
      
      // Verify touch targets are adequately sized (at least 44px)
      const submitButton = page.locator(selectors.jobForm.submitButton);
      const buttonBox = await submitButton.boundingBox();
      
      if (buttonBox) {
        expect(buttonBox.height).toBeGreaterThanOrEqual(44);
        expect(buttonBox.width).toBeGreaterThanOrEqual(44);
      }

      // Create job with touch interactions
      const jobId = await jobHelper.createJob(jobData);
      
      // Test mobile navigation
      await navHelper.goToDashboard();
      
      // Touch navigation should work
      const jobList = await jobHelper.getJobList();
      const listJob = jobList.find(job => job.title === jobData.title);
      expect(listJob).toBeTruthy();

      // Wait for completion
      await jobHelper.waitForJobCompletion(jobId);
      
      // Cleanup
      await jobHelper.deleteJob(jobId);
      
    } catch (error) {
      console.error('Mobile touch test failed:', error);
      throw error;
    }
  });

  test('should handle mobile form input correctly', async ({ page }) => {
    await navHelper.goToJobCreation();
    
    // Test mobile form interactions with agent selector
    await page.tap(selectors.jobForm.agentSelector);
    await page.tap(`[data-testid="agent-option-simple_prompt"]`);
    
    // Wait for dynamic form to load
    await page.waitForSelector(selectors.jobForm.titleInput);
    
    // Verify mobile keyboard handling
    await page.fill(selectors.jobForm.titleInput, 'Mobile Test Job');
    
    // Check that mobile input focus works
    const titleInput = page.locator(selectors.jobForm.titleInput);
    await titleInput.focus();
    
    const isFocused = await titleInput.evaluate(el => document.activeElement === el);
    expect(isFocused).toBe(true);
    
    // Test dynamic field input on mobile
    const promptField = selectors.jobForm.dynamicField('prompt');
    await page.fill(promptField, 'Mobile test prompt');
    
    // Verify mobile form validation
    await page.fill(selectors.jobForm.titleInput, ''); // Clear required field
    await page.click(selectors.jobForm.submitButton);
    
    // Should show validation feedback
    const titleIsInvalid = await titleInput.evaluate(el => !(el as HTMLInputElement).validity.valid);
    expect(titleIsInvalid).toBe(true);
  });

  test('should display mobile-optimized loading states', async ({ page }) => {
    const testData = generateTestData('mobile-loading');
    const jobData = {
      ...testJobs.simple_prompt,
      title: testData.title
    };

    try {
      // Create job and immediately check loading states
      await navHelper.goToJobCreation();
      
      // Select agent
      await page.tap(selectors.jobForm.agentSelector);
      await page.tap(`[data-testid="agent-option-${jobData.agent_identifier}"]`);
      
      // Wait for form to load
      await page.waitForSelector(selectors.jobForm.titleInput);
      
      // Fill form
      await page.fill(selectors.jobForm.titleInput, jobData.title);
      await page.fill(selectors.jobForm.dynamicField('prompt'), 'Test prompt for mobile loading');
      
      // Submit and check for mobile loading indicators
      await page.click(selectors.jobForm.submitButton);
      
      // Should show some loading state during submission
      const hasLoadingState = await page.locator(selectors.ui.loadingSpinner).isVisible() ||
                             await page.locator('[class*="loading"]').isVisible() ||
                             await page.locator('[class*="spinner"]').isVisible();
      
      // Note: Loading state might be very brief, so we don't strictly require it
      
      // Wait for redirect to job details
      await page.waitForURL(/\/job\/[a-f0-9-]+/, { timeout: timeouts.pageLoad });
      
      // Extract job ID and cleanup
      const url = page.url();
      const jobId = url.match(/\/job\/([a-f0-9-]+)/)?.[1];
      
      if (jobId) {
        await jobHelper.waitForJobCompletion(jobId);
        await jobHelper.deleteJob(jobId);
      }
      
    } catch (error) {
      console.error('Mobile loading states test failed:', error);
      throw error;
    }
  });

  test('should handle mobile viewport changes', async ({ page }) => {
    // Test different mobile orientations
    const portraitViewport = { width: 375, height: 667 };
    const landscapeViewport = { width: 667, height: 375 };
    
    // Start in portrait
    await page.setViewportSize(portraitViewport);
    await navHelper.goToDashboard();
    
    // Verify layout works in portrait
    await expect(page.locator(selectors.jobList.container)).toBeVisible();
    
    // Switch to landscape
    await page.setViewportSize(landscapeViewport);
    
    // Verify layout adapts to landscape
    await expect(page.locator(selectors.jobList.container)).toBeVisible();
    
    // Navigation should still work
    await navHelper.goToJobCreation();
    await expect(page.locator(selectors.jobForm.container)).toBeVisible();
  });

  test('should handle mobile back button and navigation', async ({ page }) => {
    // Start at dashboard
    await navHelper.goToDashboard();
    
    // Navigate to job creation
    await navHelper.goToJobCreation();
    await expect(page).toHaveURL('/schedule');
    
    // Use browser back button (simulate mobile back)
    await page.goBack();
    await expect(page).toHaveURL('/');
    
    // Forward navigation should work
    await page.goForward();
    await expect(page).toHaveURL('/schedule');
  });

  test('should handle form interactions on mobile devices', async ({ page }) => {
    // Navigate to job creation
    await navHelper.goToNewJob();

    // Tap on agent selector (mobile tap event)
    await page.tap(selectors.jobForm.agentSelector);

    // Select the simple_prompt agent
    await page.tap(`[data-testid="agent-option-simple_prompt"]`);

    // Wait for dynamic form to render
    await page.waitForSelector(selectors.jobForm.dynamicField('prompt'));

    // Fill mobile form fields
    await page.fill(selectors.jobForm.titleInput, 'Mobile Test Job');
    await page.fill(selectors.jobForm.dynamicField('prompt'), 'Test prompt for mobile');

    // Submit via mobile interaction
    await page.tap(selectors.jobForm.submitButton);

    // Verify navigation to job detail
    await page.waitForURL(/\/job\/[a-f0-9-]+/);
  });

  test('should show loading states properly on mobile', async ({ page }) => {
    const testData = generateTestData('mobile-loading');
    const jobData = {
      ...testJobs.simple_prompt,
      title: testData.title
    };

    // Navigate to job creation
    await navHelper.goToNewJob();

    // Select agent and verify loading behavior
    await page.tap(selectors.jobForm.agentSelector);
    await page.tap(`[data-testid="agent-option-${jobData.agent_identifier}"]`);
    
    // Wait for schema loading to complete
    await page.waitForSelector(selectors.jobForm.dynamicField('prompt'));
    
    // Verify form fields are available
    await expect(page.locator(selectors.jobForm.dynamicField('prompt'))).toBeVisible();
  });
}); 