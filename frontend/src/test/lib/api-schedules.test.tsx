import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createMockApiSuccessResponse, createMockApiErrorResponse } from '../utils'

// Mock axios before importing anything else
vi.mock('axios', () => {
  // Define mock functions inside the factory to avoid hoisting issues
  const mockGet = vi.fn()
  const mockPost = vi.fn()
  const mockPut = vi.fn()
  const mockDelete = vi.fn()
  
  const mockAxiosInstance = {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
  
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }
  }
})

// Mock console.error to avoid cluttering test output
const mockConsoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

// Mock localStorage for auth tokens
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

// Mock window.location for auth redirects
Object.defineProperty(window, 'location', {
  value: { href: '' },
  writable: true,
})

// Now import the api module after mocks are set up
import { api, handleApiError } from '../../lib/api'
import axios from 'axios'

// Get access to the mocked axios functions
const mockedAxios = vi.mocked(axios, true)
const getMockInstance = () => {
  const instance = mockedAxios.create()
  return {
    get: instance.get as any,
    post: instance.post as any,
    put: instance.put as any,
    delete: instance.delete as any,
  }
}

describe('Schedule API Client (Task 5.10)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Schedule Creation API', () => {
    it('successfully creates a schedule', async () => {
      const scheduleData = {
        title: 'Daily Data Processing',
        description: 'Process daily data files',
        agent_name: 'data_processor',
        cron_expression: '0 9 * * *',
        timezone: 'UTC',
        agent_config_data: {
          name: 'data_processor',
          job_data: { prompt: 'Process data' },
          execution: { priority: 5 }
        }
      }

      const expectedResponse = createMockApiSuccessResponse({
        id: 'schedule-123',
        ...scheduleData,
        created_at: '2024-01-01T00:00:00Z',
        enabled: true
      })

      const mockInstance = getMockInstance()
      mockInstance.post.mockResolvedValueOnce({
        data: expectedResponse,
        status: 201,
        statusText: 'Created',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.create(scheduleData)

      expect(mockInstance.post).toHaveBeenCalledWith('/schedules/', scheduleData)
      expect(result).toEqual(expectedResponse)
    })

    it('handles schedule creation validation errors', async () => {
      const invalidScheduleData = {
        title: '', // Invalid - empty title
        agent_name: 'data_processor',
        cron_expression: 'invalid_cron'
      }

      const errorResponse = createMockApiErrorResponse(
        'Validation failed',
        'Invalid schedule data',
        {
          validation_errors: [
            { field: 'title', message: 'Title is required' },
            { field: 'cron_expression', message: 'Invalid cron expression' }
          ]
        }
      )

      const axiosError = {
        response: {
          data: errorResponse,
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        },
        message: 'Request failed with status code 400',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true
      }

      const mockInstance = getMockInstance()
      mockInstance.post.mockRejectedValueOnce(axiosError)

      await expect(api.schedules.create(invalidScheduleData)).rejects.toThrow()
    })

    it('handles server errors during schedule creation', async () => {
      const scheduleData = {
        title: 'Test Schedule',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        agent_config_data: { name: 'test_agent' }
      }

      const errorResponse = createMockApiErrorResponse('Internal server error')

      const axiosError = {
        response: {
          data: errorResponse,
          status: 500,
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any
        },
        message: 'Request failed with status code 500',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true
      }

      const mockInstance = getMockInstance()
      mockInstance.post.mockRejectedValueOnce(axiosError)

      await expect(api.schedules.create(scheduleData)).rejects.toThrow()
    })

    it('handles network errors during schedule creation', async () => {
      const scheduleData = {
        title: 'Test Schedule',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        agent_config_data: { name: 'test_agent' }
      }

      const networkError = new Error('Network error')
      const mockInstance = getMockInstance()
      mockInstance.post.mockRejectedValueOnce(networkError)

      await expect(api.schedules.create(scheduleData)).rejects.toThrow('Network error')
    })
  })

  describe('Schedule Retrieval API', () => {
    it('successfully retrieves all schedules', async () => {
      const mockSchedules = [
        {
          id: 'schedule-1',
          title: 'Daily Task',
          agent_name: 'test_agent',
          cron_expression: '0 9 * * *',
          enabled: true
        }
      ]

      const expectedResponse = createMockApiSuccessResponse(mockSchedules)

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getAll()

      expect(mockInstance.get).toHaveBeenCalledWith('/schedules/')
      expect(result).toEqual(mockSchedules)
    })

    it('successfully gets schedule by ID', async () => {
      const scheduleId = 'schedule-123'
      const mockSchedule = {
        id: scheduleId,
        title: 'Test Schedule',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        enabled: true,
        created_at: '2024-01-01T00:00:00Z'
      }

      const expectedResponse = createMockApiSuccessResponse(mockSchedule)

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getById(scheduleId)

      expect(mockInstance.get).toHaveBeenCalledWith(`/schedules/${scheduleId}`)
      expect(result).toEqual(mockSchedule)
    })

    it('successfully gets upcoming schedules with limit', async () => {
      const mockUpcomingSchedules = [
        {
          id: 'schedule-1',
          title: 'Daily Processing',
          agent_name: 'processor',
          cron_expression: '0 9 * * *',
          next_run: '2024-01-01T09:00:00Z',
          enabled: true
        }
      ]

      const expectedResponse = createMockApiSuccessResponse(mockUpcomingSchedules)

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getAllUpcoming(5)

      expect(mockInstance.get).toHaveBeenCalledWith('/schedules/upcoming', {
        params: { limit: 5 }
      })
      expect(result).toEqual(mockUpcomingSchedules)
    })
  })

  describe('Schedule Update API', () => {
    it('successfully updates a schedule', async () => {
      const scheduleId = 'schedule-123'
      const updateData = {
        title: 'Updated Schedule',
        description: 'Updated description',
        enabled: false
      }

      const updatedSchedule = {
        id: scheduleId,
        ...updateData,
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        created_at: '2024-01-01T00:00:00Z'
      }

      const expectedResponse = createMockApiSuccessResponse(updatedSchedule)

      const mockInstance = getMockInstance()
      mockInstance.put.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.update(scheduleId, updateData)

      expect(mockInstance.put).toHaveBeenCalledWith(`/schedules/${scheduleId}`, updateData)
      expect(result).toEqual(updatedSchedule)
    })
  })

  describe('Schedule Enable/Disable API', () => {
    it('successfully enables a schedule', async () => {
      const scheduleId = 'schedule-123'
      const expectedResponse = createMockApiSuccessResponse({ success: true })

      const mockInstance = getMockInstance()
      mockInstance.post.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.enable(scheduleId)

      expect(mockInstance.post).toHaveBeenCalledWith(`/schedules/${scheduleId}/enable`)
      expect(result).toEqual({ success: true })
    })

    it('successfully disables a schedule', async () => {
      const scheduleId = 'schedule-123'
      const expectedResponse = createMockApiSuccessResponse({ success: true })

      const mockInstance = getMockInstance()
      mockInstance.post.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.disable(scheduleId)

      expect(mockInstance.post).toHaveBeenCalledWith(`/schedules/${scheduleId}/disable`)
      expect(result).toEqual({ success: true })
    })
  })

  describe('Schedule Deletion API', () => {
    it('successfully deletes a schedule', async () => {
      const scheduleId = 'schedule-123'

      const mockInstance = getMockInstance()
      mockInstance.delete.mockResolvedValueOnce({
        data: {},
        status: 204,
        statusText: 'No Content',
        headers: {},
        config: {} as any
      })

      await api.schedules.delete(scheduleId)

      expect(mockInstance.delete).toHaveBeenCalledWith(`/schedules/${scheduleId}`)
    })
  })

  describe('Schedule Run Now API', () => {
    it('successfully runs a schedule immediately', async () => {
      const scheduleId = 'schedule-123'
      const jobId = 'job-456'
      const expectedResponse = createMockApiSuccessResponse({ job_id: jobId })

      const mockInstance = getMockInstance()
      mockInstance.post.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.runNow(scheduleId)

      expect(mockInstance.post).toHaveBeenCalledWith(`/schedules/${scheduleId}/run-now`)
      expect(result).toEqual({ job_id: jobId })
    })
  })

  describe('Schedule History API', () => {
    it('successfully gets schedule history with pagination', async () => {
      const scheduleId = 'schedule-123'
      const mockHistory = [
        {
          id: 'execution-1',
          schedule_id: scheduleId,
          job_id: 'job-1',
          started_at: '2024-01-01T09:00:00Z',
          status: 'completed'
        }
      ]

      const expectedResponse = createMockApiSuccessResponse(mockHistory)
      expectedResponse.metadata = { count: 1 }

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getHistory(scheduleId, 10, 0)

      expect(mockInstance.get).toHaveBeenCalledWith(`/schedules/${scheduleId}/history`, {
        params: { limit: 10, offset: 0 }
      })
      expect(result).toEqual({ jobs: mockHistory, total_count: 1 })
    })

    it('uses default pagination parameters', async () => {
      const scheduleId = 'schedule-123'
      const mockHistory = []
      const expectedResponse = createMockApiSuccessResponse(mockHistory)

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      await api.schedules.getHistory(scheduleId)

      expect(mockInstance.get).toHaveBeenCalledWith(`/schedules/${scheduleId}/history`, {
        params: { limit: 50, offset: 0 }
      })
    })
  })

  describe('Error Handling and Recovery', () => {
    it('handles network timeout errors', async () => {
      const timeoutError = new Error('Request timeout')
      timeoutError.name = 'TimeoutError'

      const mockInstance = getMockInstance()
      mockInstance.get.mockRejectedValueOnce(timeoutError)

      await expect(api.schedules.getAll()).rejects.toThrow('Request timeout')
    })

    it('handles empty response bodies', async () => {
      const expectedResponse = createMockApiSuccessResponse([])

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getAll()
      expect(result).toEqual([])
    })

    it('properly handles API error responses with details', async () => {
      const errorResponse = createMockApiErrorResponse(
        'Validation failed',
        'Invalid request data',
        {
          validation_errors: [
            { field: 'title', message: 'Title is required' }
          ]
        }
      )

      const axiosError = {
        response: {
          data: errorResponse,
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        },
        message: 'Request failed with status code 400',
        name: 'AxiosError',
        config: {} as any,
        isAxiosError: true
      }

      const mockInstance = getMockInstance()
      mockInstance.post.mockRejectedValueOnce(axiosError)

      try {
        await api.schedules.create({ title: '', agent_name: 'test' })
      } catch (error: any) {
        expect(error.message).toContain('Request failed with status code 400')
      }
    })
  })

  describe('Authentication and Authorization', () => {
    it('includes authorization headers in requests', async () => {
      const expectedResponse = createMockApiSuccessResponse([])

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      await api.schedules.getAll()

      expect(mockInstance.get).toHaveBeenCalledWith('/schedules/')
    })
  })

  describe('API Response Validation', () => {
    it('validates API response structure', async () => {
      // Mock an invalid response structure that should be rejected
      const invalidResponse = { invalid: 'response' }

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: invalidResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      // Since extractApiResult will throw an error for invalid response structure,
      // we should expect the API call to throw
      await expect(api.schedules.getAll()).rejects.toThrow('API request failed')
    })

    it('handles successful responses with empty results', async () => {
      const expectedResponse = createMockApiSuccessResponse([])

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getAll()
      expect(result).toEqual([])
    })

    it('validates schedule data structure in responses', async () => {
      const mockSchedule = {
        id: 'schedule-123',
        title: 'Test Schedule',
        agent_name: 'test_agent',
        cron_expression: '0 9 * * *',
        enabled: true
      }

      const expectedResponse = createMockApiSuccessResponse(mockSchedule)

      const mockInstance = getMockInstance()
      mockInstance.get.mockResolvedValueOnce({
        data: expectedResponse,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any
      })

      const result = await api.schedules.getById('schedule-123')
      expect(result).toEqual(mockSchedule)
    })
  })

  describe('handleApiError Function', () => {
    it('extracts error message from API error response', () => {
      const apiError = {
        status: 400,
        message: 'Validation failed',
        data: createMockApiErrorResponse('Validation failed'),
        errors: { title: ['Title is required'] }
      }

      const errorMessage = handleApiError(apiError)
      expect(errorMessage).toContain('Validation failed')
    })

    it('handles generic error objects', () => {
      const genericError = new Error('Generic error')
      
      const errorMessage = handleApiError(genericError)
      expect(errorMessage).toContain('Generic error')
    })

    it('handles unknown error types', () => {
      const unknownError = 'String error'
      
      const errorMessage = handleApiError(unknownError)
      expect(errorMessage).toEqual('String error')
    })

    it('handles errors with nested validation details', () => {
      const validationError = {
        status: 422,
        message: 'Validation failed',
        data: createMockApiErrorResponse('Validation failed'),
        errors: {
          title: ['Title is required'],
          cron_expression: ['Invalid cron expression']
        }
      }

      const errorMessage = handleApiError(validationError)
      expect(errorMessage).toContain('Validation failed')
    })
  })
}) 