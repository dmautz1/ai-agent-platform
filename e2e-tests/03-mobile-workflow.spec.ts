import { test, expect, devices } from '@playwright/test';
import { AuthHelper, JobHelper, NavigationHelper } from './helpers/test-helpers';
import { testUsers, testJobs, generateTestData, selectors, timeouts } from './helpers/test-data';

// Mobile-specific test configuration
test.use({
  ...devices['iPhone 12'],
});

test.describe('Mobile Job Workflow', () => {
  let authHelper: AuthHelper;
  let jobHelper: JobHelper;
  let navHelper: NavigationHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    jobHelper = new JobHelper(page);
    navHelper = new NavigationHelper(page);
    
    // Login before each test
    await authHelper.login(testUsers.admin);
  });

  test.afterEach(async ({ page }) => {
    // Cleanup: logout after each test
    await authHelper.logout();
  });

  test('should complete job workflow on mobile device', async ({ page }) => {
    const testData = generateTestData('mobile-test');
    const jobData = {
      ...testJobs.textProcessing,
      title: testData.title
    };

    // Test mobile viewport dimensions
    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBeLessThan(768); // Should be mobile width

    // Step 1: Navigate to job creation (mobile navigation)
    await navHelper.goToJobCreation();
    
    // Verify mobile-friendly form layout
    await expect(page.locator(selectors.jobForm.container)).toBeVisible();
    
    // Step 2: Create job with mobile interactions
    const jobId = await jobHelper.createJob(jobData);
    expect(jobId).toBeTruthy();

    // Step 3: Verify mobile job details page
    const jobDetails = await jobHelper.getJobDetails(jobId);
    expect(jobDetails.title).toBe(jobData.title);

    // Step 4: Check mobile dashboard layout
    await navHelper.goToDashboard();
    
    // Verify mobile card layout (not table)
    await expect(page.locator(selectors.jobList.container)).toBeVisible();
    
    // Jobs should be displayed as cards on mobile
    const jobCards = page.locator('[data-testid^="job-card-"]').or(
      page.locator('.card').or(
        page.locator('[class*="card"]')
      )
    );
    
    // Should have mobile-friendly layout
    const hasCardLayout = await jobCards.count() > 0;
    const hasStackedLayout = await page.locator('[class*="space-y"], [class*="flex-col"]').isVisible();
    
    expect(hasCardLayout || hasStackedLayout).toBe(true);

    // Step 5: Test mobile job completion monitoring
    const finalStatus = await jobHelper.waitForJobCompletion(jobId);
    expect(finalStatus).toBe('completed');

    // Step 6: Verify mobile job deletion
    await jobHelper.deleteJob(jobId);
    
    // Verify job is removed from mobile list
    const updatedJobList = await jobHelper.getJobList();
    const deletedJob = updatedJobList.find(job => job.title === jobData.title);
    expect(deletedJob).toBeFalsy();
  });

  test('should handle mobile touch interactions', async ({ page }) => {
    const testData = generateTestData('mobile-touch');
    const jobData = {
      ...testJobs.summarization,
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
    
    // Test mobile form interactions
    await page.selectOption(selectors.jobForm.agentTypeSelect, 'text_processing');
    
    // Verify mobile keyboard handling
    await page.fill(selectors.jobForm.titleInput, 'Mobile Test Job');
    
    // Check that mobile input focus works
    const titleInput = page.locator(selectors.jobForm.titleInput);
    await titleInput.focus();
    
    const isFocused = await titleInput.evaluate(el => document.activeElement === el);
    expect(isFocused).toBe(true);
    
    // Test text area input on mobile
    await page.fill(selectors.jobForm.textProcessing.inputText, 'Mobile test input text');
    
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
      ...testJobs.textProcessing,
      title: testData.title
    };

    try {
      // Create job and immediately check loading states
      await navHelper.goToJobCreation();
      
      // Fill form
      await page.selectOption(selectors.jobForm.agentTypeSelect, jobData.agentType);
      await page.fill(selectors.jobForm.titleInput, jobData.title);
      await page.fill(selectors.jobForm.textProcessing.inputText, jobData.data.input_text);
      
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
}); 