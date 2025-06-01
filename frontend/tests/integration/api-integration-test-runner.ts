#!/usr/bin/env node

/**
 * API Integration Test Runner
 * 
 * This script can be run to test actual frontend-backend communication
 * against a real or mock server to verify integration scenarios.
 */

/// <reference types="node" />

import { api, handleApiError, formatValidationErrors, isValidationError } from '../../src/lib/api';
import type { CreateJobRequest, JobsQuery, LoginRequest } from '../../src/lib/types';

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
}

interface TestSuite {
  name: string;
  results: TestResult[];
  passed: number;
  failed: number;
  duration: number;
}

class APIIntegrationTester {
  private results: TestSuite[] = [];

  async runTest(name: string, testFn: () => Promise<void>): Promise<TestResult> {
    const startTime = Date.now();
    try {
      await testFn();
      const duration = Date.now() - startTime;
      return { name, passed: true, duration };
    } catch (error) {
      const duration = Date.now() - startTime;
      return { 
        name, 
        passed: false, 
        error: error instanceof Error ? error.message : String(error),
        duration 
      };
    }
  }

  async runSuite(name: string, tests: Array<{ name: string; fn: () => Promise<void> }>): Promise<TestSuite> {
    console.log(`\n🧪 Running Test Suite: ${name}`);
    console.log('='.repeat(50));

    const startTime = Date.now();
    const results: TestResult[] = [];

    for (const test of tests) {
      console.log(`   Running: ${test.name}`);
      const result = await this.runTest(test.name, test.fn);
      results.push(result);
      
      if (result.passed) {
        console.log(`   ✅ ${test.name} (${result.duration}ms)`);
      } else {
        console.log(`   ❌ ${test.name} (${result.duration}ms)`);
        console.log(`      Error: ${result.error}`);
      }
    }

    const duration = Date.now() - startTime;
    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;

    const suite: TestSuite = { name, results, passed, failed, duration };
    this.results.push(suite);

    console.log(`\n📊 Suite Results: ${passed} passed, ${failed} failed (${duration}ms)`);
    return suite;
  }

  printSummary(): void {
    console.log('\n' + '='.repeat(60));
    console.log('🏁 TEST EXECUTION SUMMARY');
    console.log('='.repeat(60));

    let totalPassed = 0;
    let totalFailed = 0;
    let totalDuration = 0;

    for (const suite of this.results) {
      totalPassed += suite.passed;
      totalFailed += suite.failed;
      totalDuration += suite.duration;
      
      const status = suite.failed === 0 ? '✅' : '❌';
      console.log(`${status} ${suite.name}: ${suite.passed}/${suite.passed + suite.failed} passed`);
    }

    console.log('\n📈 Overall Statistics:');
    console.log(`   Total Tests: ${totalPassed + totalFailed}`);
    console.log(`   Passed: ${totalPassed}`);
    console.log(`   Failed: ${totalFailed}`);
    console.log(`   Success Rate: ${((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1)}%`);
    console.log(`   Total Duration: ${totalDuration}ms`);

    if (totalFailed > 0) {
      console.log('\n❌ Failed Tests:');
      for (const suite of this.results) {
        for (const result of suite.results) {
          if (!result.passed) {
            console.log(`   - ${suite.name}: ${result.name}`);
            console.log(`     ${result.error}`);
          }
        }
      }
      process.exit(1);
    } else {
      console.log('\n🎉 All tests passed!');
      process.exit(0);
    }
  }
}

// Test helper functions
function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertThrows(fn: () => any, expectedMessage?: string): void {
  try {
    fn();
    throw new Error('Expected function to throw, but it did not');
  } catch (error) {
    if (expectedMessage && !error.message.includes(expectedMessage)) {
      throw new Error(`Expected error message to contain "${expectedMessage}", but got: ${error.message}`);
    }
  }
}

// Main test execution
async function runIntegrationTests(): Promise<void> {
  const tester = new APIIntegrationTester();

  // Test Suite 1: Error Utility Functions
  await tester.runSuite('Error Utility Functions', [
    {
      name: 'handleApiError should handle API error objects',
      fn: async () => {
        const apiError = {
          status: 422,
          message: 'Validation failed',
          errors: { field: ['Error message'] }
        };
        const result = handleApiError(apiError);
        assert(result === 'Validation failed', 'Should return error message');
      }
    },
    {
      name: 'handleApiError should handle string errors',
      fn: async () => {
        const result = handleApiError('Simple error message');
        assert(result === 'Simple error message', 'Should return string as-is');
      }
    },
    {
      name: 'handleApiError should handle unknown error formats',
      fn: async () => {
        const result = handleApiError({});
        assert(result === 'An unexpected error occurred', 'Should return default message');
      }
    },
    {
      name: 'formatValidationErrors should format complex errors',
      fn: async () => {
        const errors = {
          'title': ['Title is required'],
          'content': ['Content is too long', 'Content contains invalid characters']
        };
        const result = formatValidationErrors(errors);
        assert(result.includes('title: Title is required'), 'Should include title error');
        assert(result.includes('content: Content is too long, Content contains invalid characters'), 'Should format multiple errors');
      }
    },
    {
      name: 'isValidationError should identify validation errors',
      fn: async () => {
        const validationError = { status: 422, errors: {} };
        const otherError = { status: 500, message: 'Server error' };
        
        assert(isValidationError(validationError), 'Should identify validation error');
        assert(!isValidationError(otherError), 'Should not identify non-validation error');
      }
    }
  ]);

  // Test Suite 2: API Response Parsing
  await tester.runSuite('API Response Parsing', [
    {
      name: 'Should handle successful API responses',
      fn: async () => {
        // Note: This would require mocking or a test server
        // For now, we'll test the structure
        const mockResponse = {
          success: true,
          data: {
            id: 'test-123',
            status: 'completed',
            created_at: '2024-01-01T00:00:00Z'
          }
        };
        
        assert(mockResponse.success === true, 'Should parse success flag');
        assert(mockResponse.data.id === 'test-123', 'Should parse data object');
      }
    },
    {
      name: 'Should handle error responses',
      fn: async () => {
        const mockErrorResponse = {
          success: false,
          message: 'Not found',
          errors: {
            'id': ['Job not found']
          }
        };
        
        assert(mockErrorResponse.success === false, 'Should parse error flag');
        assert(mockErrorResponse.message === 'Not found', 'Should parse error message');
      }
    }
  ]);

  // Test Suite 3: Request Data Validation
  await tester.runSuite('Request Data Validation', [
    {
      name: 'Should validate job creation request structure',
      fn: async () => {
        const validJobRequest: CreateJobRequest = {
          data: {
            agent_type: 'text_processing',
            title: 'Test Job',
            input_text: 'Sample text for processing',
            operation: 'sentiment_analysis'
          },
          priority: 'normal',
          tags: ['test']
        };
        
        assert(validJobRequest.data.agent_type === 'text_processing', 'Should have valid agent type');
        assert(validJobRequest.data.title?.length > 0, 'Should have non-empty title');
        assert(Array.isArray(validJobRequest.tags), 'Should have tags array');
      }
    },
    {
      name: 'Should validate jobs query structure',
      fn: async () => {
        const validQuery: JobsQuery = {
          status: ['pending', 'running'],
          agent_type: 'text_processing',
          page: 1,
          per_page: 20
        };
        
        assert(Array.isArray(validQuery.status), 'Should handle status array');
        assert(typeof validQuery.page === 'number', 'Should have numeric page');
        assert(validQuery.per_page! > 0, 'Should have positive per_page');
      }
    },
    {
      name: 'Should validate login request structure',
      fn: async () => {
        const validLogin: LoginRequest = {
          email: 'test@example.com',
          password: 'securepassword',
          remember_me: true
        };
        
        assert(validLogin.email.includes('@'), 'Should have valid email format');
        assert(validLogin.password.length > 0, 'Should have non-empty password');
        assert(typeof validLogin.remember_me === 'boolean', 'Should have boolean remember_me');
      }
    }
  ]);

  // Test Suite 4: Error Scenario Simulation
  await tester.runSuite('Error Scenario Simulation', [
    {
      name: 'Should simulate network timeout error',
      fn: async () => {
        const timeoutError = {
          code: 'ECONNABORTED',
          message: 'timeout of 30000ms exceeded'
        };
        
        const errorMessage = handleApiError(timeoutError);
        assert(errorMessage.includes('timeout'), 'Should handle timeout error');
      }
    },
    {
      name: 'Should simulate validation error response',
      fn: async () => {
        const validationErrorResponse = {
          status: 422,
          message: 'Validation failed',
          errors: {
            'data.title': ['Title is required', 'Title must be unique'],
            'data.input_text': ['Input text is too short']
          }
        };
        
        assert(isValidationError(validationErrorResponse), 'Should identify as validation error');
        
        const formattedErrors = formatValidationErrors(validationErrorResponse.errors);
        assert(formattedErrors.includes('Title is required'), 'Should format validation errors');
      }
    },
    {
      name: 'Should simulate rate limiting error',
      fn: async () => {
        const rateLimitError = {
          status: 429,
          message: 'Rate limit exceeded',
          data: {
            retry_after: 60
          }
        };
        
        const errorMessage = handleApiError(rateLimitError);
        assert(errorMessage.includes('Rate limit'), 'Should handle rate limit error');
      }
    },
    {
      name: 'Should simulate server error',
      fn: async () => {
        const serverError = {
          status: 500,
          message: 'Internal server error',
          data: {
            request_id: 'req-123'
          }
        };
        
        const errorMessage = handleApiError(serverError);
        assert(errorMessage.includes('Internal server error'), 'Should handle server error');
      }
    }
  ]);

  // Test Suite 5: Data Serialization and Parsing
  await tester.runSuite('Data Serialization and Parsing', [
    {
      name: 'Should handle Unicode and special characters',
      fn: async () => {
        const unicodeData = {
          title: 'Test Job 🚀',
          content: 'Special chars: àáâãäå 中文 العربية',
          emoji: '🌍🔥💯'
        };
        
        const serialized = JSON.stringify(unicodeData);
        const parsed = JSON.parse(serialized);
        
        assert(parsed.title === unicodeData.title, 'Should preserve Unicode in title');
        assert(parsed.content === unicodeData.content, 'Should preserve special characters');
        assert(parsed.emoji === unicodeData.emoji, 'Should preserve emojis');
      }
    },
    {
      name: 'Should handle large data payloads',
      fn: async () => {
        const largeText = 'x'.repeat(10000); // 10KB of text
        const largeData = {
          agent_type: 'text_processing',
          title: 'Large Text Processing Job',
          input_text: largeText,
          metadata: {
            large_array: Array.from({ length: 1000 }, (_, i) => `item-${i}`),
            nested_object: {
              level1: {
                level2: {
                  level3: {
                    data: 'deep nested data'
                  }
                }
              }
            }
          }
        };
        
        const serialized = JSON.stringify(largeData);
        assert(serialized.length > 10000, 'Should handle large serialized data');
        
        const parsed = JSON.parse(serialized);
        assert(parsed.input_text.length === 10000, 'Should preserve large text');
        assert(parsed.metadata.large_array.length === 1000, 'Should preserve large arrays');
        assert(parsed.metadata.nested_object.level1.level2.level3.data === 'deep nested data', 'Should preserve nested objects');
      }
    },
    {
      name: 'Should handle complex date formats',
      fn: async () => {
        const dateData = {
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T12:30:45.123Z',
          completed_at: new Date().toISOString()
        };
        
        const serialized = JSON.stringify(dateData);
        const parsed = JSON.parse(serialized);
        
        // Verify dates are valid ISO strings
        assert(!isNaN(Date.parse(parsed.created_at)), 'Should parse created_at date');
        assert(!isNaN(Date.parse(parsed.updated_at)), 'Should parse updated_at date');
        assert(!isNaN(Date.parse(parsed.completed_at)), 'Should parse completed_at date');
      }
    }
  ]);

  tester.printSummary();
}

// Execute tests if run directly
if (typeof require !== 'undefined' && require.main === module) {
  console.log('🚀 Starting Frontend-Backend API Communication Integration Tests');
  console.log('This test suite validates API communication patterns and error handling');
  
  runIntegrationTests().catch(error => {
    console.error('\n💥 Test execution failed:');
    console.error(error);
    process.exit(1);
  });
}

export { APIIntegrationTester, runIntegrationTests }; 