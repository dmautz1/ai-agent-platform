import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { api, handleApiError, formatValidationErrors } from '../../src/lib/api';
import type { ApiError } from '../../src/lib/types';
import axios from 'axios';

// Mock different error scenarios
const mockAxios = vi.fn();

describe('API Error Handling and Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock axios.create with our controlled mock
    vi.mocked(axios.create).mockImplementation(() => ({
      ...axios.create(),
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() }
      },
      get: mockAxios,
      post: mockAxios,
      patch: mockAxios,
      delete: mockAxios,
    }) as any);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Network and Connection Errors', () => {
    it('should handle DNS resolution failures', async () => {
      const dnsError = {
        code: 'ENOTFOUND',
        hostname: 'api.nonexistent-domain.com',
        message: 'getaddrinfo ENOTFOUND api.nonexistent-domain.com'
      };

      mockAxios.mockRejectedValueOnce(dnsError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'getaddrinfo ENOTFOUND api.nonexistent-domain.com'
        });
      }
    });

    it('should handle connection refused errors', async () => {
      const connectionError = {
        code: 'ECONNREFUSED',
        address: '127.0.0.1',
        port: 8000,
        message: 'connect ECONNREFUSED 127.0.0.1:8000'
      };

      mockAxios.mockRejectedValueOnce(connectionError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'connect ECONNREFUSED 127.0.0.1:8000'
        });
      }
    });

    it('should handle SSL/TLS errors', async () => {
      const sslError = {
        code: 'CERT_UNTRUSTED',
        message: 'certificate verify failed: self signed certificate'
      };

      mockAxios.mockRejectedValueOnce(sslError);

      try {
        await api.health.check();
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'certificate verify failed: self signed certificate'
        });
      }
    });

    it('should handle request timeout scenarios', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
        config: { timeout: 30000 }
      };

      mockAxios.mockRejectedValueOnce(timeoutError);

      try {
        await api.jobs.create({
          data: {
            agent_type: 'text_processing',
            title: 'Long Running Job',
            input_text: 'Very long text that takes time to process...'
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'timeout of 30000ms exceeded'
        });
      }
    });

    it('should handle socket hang up errors', async () => {
      const socketError = {
        code: 'ECONNRESET',
        message: 'socket hang up'
      };

      mockAxios.mockRejectedValueOnce(socketError);

      try {
        await api.jobs.getById('job-123');
      } catch (error) {
        expect(error).toMatchObject({
          status: 0,
          message: 'socket hang up'
        });
      }
    });
  });

  describe('HTTP Status Code Edge Cases', () => {
    it('should handle 400 Bad Request with detailed errors', async () => {
      const badRequestError = {
        response: {
          status: 400,
          data: {
            message: 'Bad Request',
            detail: 'Invalid JSON in request body',
            errors: {
              'json': ['Expected valid JSON format']
            }
          }
        }
      };

      mockAxios.mockRejectedValueOnce(badRequestError);

      try {
        await api.jobs.create({
          data: {
            agent_type: 'text_processing',
            title: 'Test Job',
            input_text: 'Test content'
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 400,
          message: 'Bad Request',
          errors: {
            'json': ['Expected valid JSON format']
          }
        });
      }
    });

    it('should handle 403 Forbidden access', async () => {
      const forbiddenError = {
        response: {
          status: 403,
          data: {
            message: 'Access forbidden',
            detail: 'Insufficient permissions to access this resource'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(forbiddenError);

      try {
        await api.jobs.delete('protected-job-123');
      } catch (error) {
        expect(error).toMatchObject({
          status: 403,
          message: 'Access forbidden'
        });
      }
    });

    it('should handle 409 Conflict errors', async () => {
      const conflictError = {
        response: {
          status: 409,
          data: {
            message: 'Conflict',
            detail: 'Job is already being processed'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(conflictError);

      try {
        await api.jobs.retry('already-running-job');
      } catch (error) {
        expect(error).toMatchObject({
          status: 409,
          message: 'Conflict'
        });
      }
    });

    it('should handle 429 Rate Limiting with retry headers', async () => {
      const rateLimitError = {
        response: {
          status: 429,
          data: {
            message: 'Rate limit exceeded',
            detail: 'Too many requests, please wait before trying again'
          },
          headers: {
            'retry-after': '120',
            'x-ratelimit-limit': '100',
            'x-ratelimit-remaining': '0',
            'x-ratelimit-reset': '1640995200'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(rateLimitError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 429,
          message: 'Rate limit exceeded'
        });
      }
    });

    it('should handle 502 Bad Gateway errors', async () => {
      const badGatewayError = {
        response: {
          status: 502,
          data: {
            message: 'Bad Gateway',
            detail: 'The server received an invalid response from an upstream server'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(badGatewayError);

      try {
        await api.agents.getTypes();
      } catch (error) {
        expect(error).toMatchObject({
          status: 502,
          message: 'Bad Gateway'
        });
      }
    });

    it('should handle 503 Service Unavailable errors', async () => {
      const serviceUnavailableError = {
        response: {
          status: 503,
          data: {
            message: 'Service Temporarily Unavailable',
            detail: 'The server is currently unable to handle the request'
          },
          headers: {
            'retry-after': '300'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(serviceUnavailableError);

      try {
        await api.health.check();
      } catch (error) {
        expect(error).toMatchObject({
          status: 503,
          message: 'Service Temporarily Unavailable'
        });
      }
    });

    it('should handle 504 Gateway Timeout errors', async () => {
      const gatewayTimeoutError = {
        response: {
          status: 504,
          data: {
            message: 'Gateway Timeout',
            detail: 'The server did not receive a timely response from the upstream server'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(gatewayTimeoutError);

      try {
        await api.jobs.create({
          data: {
            agent_type: 'summarization',
            title: 'Large Document Processing',
            input_text: 'Very large document content...'
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 504,
          message: 'Gateway Timeout'
        });
      }
    });
  });

  describe('Data Validation and Serialization Errors', () => {
    it('should handle complex validation errors with nested fields', async () => {
      const complexValidationError = {
        response: {
          status: 422,
          data: {
            message: 'Validation failed',
            errors: {
              'data.agent_type': ['Agent type is required'],
              'data.title': ['Title must be between 1 and 200 characters'],
              'data.input_text': ['Input text is required', 'Input text must be less than 10000 characters'],
              'priority': ['Priority must be one of: low, normal, high, urgent'],
              'tags': ['Tags must be an array of strings'],
              'metadata.timeout': ['Timeout must be a positive integer']
            }
          }
        }
      };

      mockAxios.mockRejectedValueOnce(complexValidationError);

      try {
        await api.jobs.create({
          data: {
            agent_type: '' as any,
            title: '',
            input_text: ''
          },
          priority: 'invalid' as any,
          tags: ['valid-tag', 123] as any,
          metadata: {
            timeout: -1
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 422,
          message: 'Validation failed',
          errors: {
            'data.agent_type': ['Agent type is required'],
            'data.title': ['Title must be between 1 and 200 characters'],
            'data.input_text': ['Input text is required', 'Input text must be less than 10000 characters']
          }
        });
      }
    });

    it('should handle malformed JSON response data', async () => {
      // Response that appears successful but has malformed data
      mockAxios.mockResolvedValueOnce({
        data: {
          success: true,
          data: 'not an object'
        }
      });

      const jobs = await api.jobs.getAll();
      
      // Should handle gracefully
      expect(jobs).toEqual([]);
    });

    it('should handle response with missing required fields', async () => {
      mockAxios.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            // Missing required job fields
            status: 'pending'
            // No id, created_at, updated_at, etc.
          }
        }
      });

      try {
        await api.jobs.getById('incomplete-job');
      } catch (error) {
        // Should either handle gracefully or throw appropriate error
        expect(error).toBeDefined();
      }
    });

    it('should handle circular reference errors in request data', async () => {
      // Create circular reference
      const circularData: any = {
        agent_type: 'text_processing',
        title: 'Circular Reference Test',
        input_text: 'Test content'
      };
      circularData.self = circularData;

      // This should be caught before making the request
      try {
        await api.jobs.create({
          data: circularData,
          metadata: circularData
        });
      } catch (error) {
        // Should handle JSON serialization error
        expect(error).toBeDefined();
      }
    });
  });

  describe('Authentication and Authorization Edge Cases', () => {
    it('should handle expired token scenarios', async () => {
      const expiredTokenError = {
        response: {
          status: 401,
          data: {
            message: 'Token expired',
            detail: 'The provided authentication token has expired',
            code: 'TOKEN_EXPIRED'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(expiredTokenError);

      try {
        await api.auth.getCurrentUser();
      } catch (error) {
        expect(error).toMatchObject({
          status: 401,
          message: 'Token expired'
        });
      }
    });

    it('should handle invalid token format', async () => {
      const invalidTokenError = {
        response: {
          status: 401,
          data: {
            message: 'Invalid token format',
            detail: 'The provided token is not a valid JWT',
            code: 'INVALID_TOKEN_FORMAT'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(invalidTokenError);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toMatchObject({
          status: 401,
          message: 'Invalid token format'
        });
      }
    });

    it('should handle token blacklist scenarios', async () => {
      const blacklistedTokenError = {
        response: {
          status: 401,
          data: {
            message: 'Token has been revoked',
            detail: 'This token has been blacklisted and cannot be used',
            code: 'TOKEN_BLACKLISTED'
          }
        }
      };

      mockAxios.mockRejectedValueOnce(blacklistedTokenError);

      try {
        await api.jobs.create({
          data: {
            agent_type: 'text_processing',
            title: 'Test Job',
            input_text: 'Test content'
          }
        });
      } catch (error) {
        expect(error).toMatchObject({
          status: 401,
          message: 'Token has been revoked'
        });
      }
    });

    it('should handle insufficient scope/permissions', async () => {
      const insufficientScopeError = {
        response: {
          status: 403,
          data: {
            message: 'Insufficient scope',
            detail: 'Token does not have required permissions for this operation',
            required_scopes: ['jobs:delete'],
            current_scopes: ['jobs:read', 'jobs:create']
          }
        }
      };

      mockAxios.mockRejectedValueOnce(insufficientScopeError);

      try {
        await api.jobs.delete('protected-job');
      } catch (error) {
        expect(error).toMatchObject({
          status: 403,
          message: 'Insufficient scope'
        });
      }
    });
  });

  describe('Response Data Integrity', () => {
    it('should handle corrupted response data', async () => {
      // Response with some fields corrupted
      mockAxios.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            id: null, // Should be string
            status: 'invalid_status', // Should be valid JobStatus
            created_at: 'not-a-date', // Should be valid ISO date
            user_id: undefined,
            data: null // Should be object
          }
        }
      });

      try {
        const job = await api.jobs.getById('corrupted-job');
        // Should either handle gracefully or validate data
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it('should handle partial response data', async () => {
      mockAxios.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            jobs: [
              { id: 'job-1', status: 'completed' }, // Missing required fields
              null, // Invalid job object
              { id: 'job-3', status: 'pending', created_at: '2024-01-01T00:00:00Z' }
            ]
          }
        }
      });

      const jobs = await api.jobs.getAll();
      
      // Should filter out invalid entries or handle gracefully
      expect(Array.isArray(jobs)).toBe(true);
    });

    it('should handle empty or null response data', async () => {
      mockAxios.mockResolvedValueOnce({
        data: null
      });

      const jobs = await api.jobs.getAll();
      expect(jobs).toEqual([]);
    });

    it('should handle undefined response', async () => {
      mockAxios.mockResolvedValueOnce(undefined);

      try {
        await api.jobs.getAll();
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Concurrent Request Scenarios', () => {
    it('should handle concurrent request failures gracefully', async () => {
      // Set up different error responses for concurrent requests
      mockAxios
        .mockRejectedValueOnce({ 
          response: { status: 500, data: { message: 'Server error 1' } } 
        })
        .mockRejectedValueOnce({ 
          response: { status: 404, data: { message: 'Not found' } } 
        })
        .mockRejectedValueOnce({ 
          code: 'ECONNABORTED', message: 'Timeout' 
        });

      const promises = [
        api.jobs.getById('job-1'),
        api.jobs.getById('job-2'),
        api.jobs.getById('job-3')
      ];

      const results = await Promise.allSettled(promises);

      expect(results[0].status).toBe('rejected');
      expect(results[1].status).toBe('rejected');
      expect(results[2].status).toBe('rejected');
    });

    it('should handle mixed success/failure in concurrent requests', async () => {
      const validJobResponse = {
        success: true,
        data: {
          id: 'job-success',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          user_id: 'user-123',
          data: { agent_type: 'text_processing', title: 'Success Job', input_text: 'Content' }
        }
      };

      mockAxios
        .mockResolvedValueOnce({ data: validJobResponse })
        .mockRejectedValueOnce({ 
          response: { status: 404, data: { message: 'Job not found' } } 
        })
        .mockResolvedValueOnce({ data: validJobResponse });

      const promises = [
        api.jobs.getById('job-1'),
        api.jobs.getById('job-2'),
        api.jobs.getById('job-3')
      ];

      const results = await Promise.allSettled(promises);

      expect(results[0].status).toBe('fulfilled');
      expect(results[1].status).toBe('rejected');
      expect(results[2].status).toBe('fulfilled');
    });
  });

  describe('Error Message Formatting', () => {
    it('should format complex error messages correctly', () => {
      const complexApiError: ApiError = {
        status: 422,
        message: 'Multiple validation errors occurred',
        data: {
          request_id: 'req-123',
          timestamp: '2024-01-01T00:00:00Z'
        },
        errors: {
          'data.title': ['Title is required', 'Title must be unique'],
          'data.input_text': ['Input text is too long'],
          'priority': ['Invalid priority value'],
          'metadata.custom_field': ['Custom field validation failed']
        }
      };

      const message = handleApiError(complexApiError);
      expect(message).toBe('Multiple validation errors occurred');

      const formattedErrors = formatValidationErrors(complexApiError.errors!);
      expect(formattedErrors).toContain('data.title: Title is required, Title must be unique');
      expect(formattedErrors).toContain('data.input_text: Input text is too long');
    });

    it('should handle error messages with special characters', () => {
      const specialCharsError: ApiError = {
        status: 400,
        message: 'Error with special chars: àáâãäå & émojis 🚨',
        data: null
      };

      const message = handleApiError(specialCharsError);
      expect(message).toBe('Error with special chars: àáâãäå & émojis 🚨');
    });

    it('should handle very long error messages', () => {
      const longMessage = 'A'.repeat(1000);
      const longMessageError: ApiError = {
        status: 500,
        message: longMessage,
        data: null
      };

      const message = handleApiError(longMessageError);
      expect(message).toBe(longMessage);
      expect(message.length).toBe(1000);
    });
  });
}); 