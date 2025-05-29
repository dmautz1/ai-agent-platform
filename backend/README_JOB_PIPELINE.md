# Job Processing Pipeline Documentation

## Overview

The Job Processing Pipeline is a comprehensive asynchronous job execution system that provides:

- **Asynchronous Job Queue Management**: Priority-based job queuing with concurrent execution
- **Real-time Status Updates**: Live job status tracking in the database
- **Error Handling & Retry Logic**: Automatic retry with exponential backoff
- **Job Scheduling**: Support for delayed job execution
- **Performance Monitoring**: Comprehensive metrics and monitoring
- **Scalable Architecture**: Configurable worker pools and queue sizes

## Architecture

### Core Components

1. **JobPipeline**: Main pipeline orchestrator
2. **JobTask**: Internal job representation with metadata
3. **JobExecutionStatus**: Metrics and status tracking
4. **Worker Pool**: Configurable concurrent job processors
5. **Scheduler**: Handles delayed job execution
6. **Cleanup Worker**: Manages memory and old job metrics

### Job Lifecycle

```
Job Submission → Queue → Worker Assignment → Execution → Status Update → Completion
                   ↓
              Scheduler (for delayed jobs)
                   ↓
              Retry Logic (on failure)
```

## Features

### 1. Priority-Based Queuing

Jobs can be assigned priority levels:

```python
class JobPriority(int, Enum):
    LOW = 0
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10
```

### 2. Automatic Retry Mechanism

- Configurable retry attempts (default: 3)
- Exponential backoff delay
- Failure tracking and reporting

### 3. Job Scheduling

- Support for delayed execution
- Cron-like scheduling capabilities
- Time-based job queuing

### 4. Real-time Monitoring

- Live job status updates
- Performance metrics
- Success/failure rates
- Execution time tracking

## Usage

### Starting the Pipeline

The pipeline is automatically started with the application:

```python
# In main.py startup event
await start_job_pipeline()
```

### Submitting Jobs

#### Via API

```bash
# Create a new job
POST /jobs
{
    "data": {
        "agent": "text_processing",
        "text": "Sample text to process",
        "operation": "analyze_sentiment"
    },
    "priority": 5,
    "tags": ["sentiment", "analysis"]
}
```

#### Programmatically

```python
from job_pipeline import get_job_pipeline

pipeline = get_job_pipeline()

await pipeline.submit_job(
    job_id="unique-job-id",
    user_id="user-123",
    agent_name="text_processing",
    job_data={
        "text": "Sample text",
        "operation": "analyze_sentiment"
    },
    priority=JobPriority.HIGH,
    max_retries=3
)
```

### Scheduled Jobs

```python
from datetime import datetime, timedelta

# Schedule job for 1 hour from now
future_time = datetime.utcnow() + timedelta(hours=1)

await pipeline.submit_job(
    job_id="scheduled-job",
    user_id="user-123",
    agent_name="text_processing",
    job_data={"text": "Scheduled processing"},
    scheduled_at=future_time
)
```

## API Endpoints

### Job Management

#### Create Job
```
POST /jobs
Content-Type: application/json
Authorization: Bearer <token>

{
    "data": {
        "agent": "text_processing",
        "text": "Text to process"
    },
    "priority": 5,
    "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Job created and queued for processing",
    "job_id": "job_abc123"
}
```

#### List Jobs
```
GET /jobs?limit=50&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "message": "Jobs retrieved successfully",
    "jobs": [
        {
            "id": "job_abc123",
            "status": "completed",
            "data": {"text": "Sample text"},
            "result": "{\"sentiment\": \"positive\"}",
            "error_message": null,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:01:00Z"
        }
    ],
    "total_count": 1
}
```

#### Get Job Details
```
GET /jobs/{job_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "message": "Job details retrieved successfully",
    "job": {
        "id": "job_abc123",
        "status": "running",
        "data": {"text": "Sample text"},
        "result": null,
        "error_message": null,
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:30Z"
    }
}
```

#### Delete Job
```
DELETE /jobs/{job_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "message": "Job deleted successfully",
    "job_id": "job_abc123"
}
```

### Pipeline Management

#### Get Pipeline Status
```
GET /pipeline/status
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "message": "Pipeline status retrieved",
    "status": {
        "is_running": true,
        "queue_size": 5,
        "scheduled_jobs": 2,
        "active_jobs": 3,
        "max_concurrent_jobs": 5,
        "worker_count": 6,
        "metrics": {
            "active_jobs": 3,
            "completed_jobs": 150,
            "failed_jobs": 5,
            "retried_jobs": 8,
            "total_processed": 155,
            "success_rate": 96.8,
            "uptime_seconds": 3600,
            "jobs_per_minute": 2.6
        }
    },
    "timestamp": "2024-01-01T11:00:00Z"
}
```

#### Get Pipeline Metrics
```
GET /pipeline/metrics
Authorization: Bearer <token>
```

**Response:**
```json
{
    "success": true,
    "message": "Pipeline metrics retrieved",
    "metrics": {
        "completed_jobs": 150,
        "failed_jobs": 5,
        "success_rate": 96.8,
        "jobs_per_minute": 2.6
    },
    "pipeline_info": {
        "is_running": true,
        "worker_count": 6,
        "max_concurrent_jobs": 5
    },
    "timestamp": "2024-01-01T11:00:00Z"
}
```

## Job Status Values

```python
class JobStatus(str, Enum):
    pending = "pending"      # Job created, waiting in queue
    running = "running"      # Job currently being executed
    completed = "completed"  # Job finished successfully
    failed = "failed"        # Job failed permanently
```

## Configuration

### Pipeline Configuration

```python
pipeline = JobPipeline(
    max_concurrent_jobs=5,    # Number of worker threads
    max_queue_size=1000,      # Maximum jobs in queue
    cleanup_interval=300,     # Cleanup cycle in seconds
    retry_delay_base=2.0      # Exponential backoff base
)
```

### Environment Variables

```bash
# Optional pipeline configuration
JOB_PIPELINE_MAX_WORKERS=5
JOB_PIPELINE_MAX_QUEUE_SIZE=1000
JOB_PIPELINE_CLEANUP_INTERVAL=300
JOB_PIPELINE_RETRY_DELAY=2.0
```

## Error Handling

### Retry Logic

Jobs that fail are automatically retried with exponential backoff:

- **Retry 1**: 2 seconds delay
- **Retry 2**: 4 seconds delay  
- **Retry 3**: 8 seconds delay
- **After max retries**: Job marked as permanently failed

### Error Types

1. **Agent Errors**: Issues with agent execution
2. **Database Errors**: Database connection or query failures
3. **Validation Errors**: Invalid job data format
4. **System Errors**: Infrastructure or resource issues

## Monitoring and Metrics

### Key Metrics

- **Active Jobs**: Currently executing jobs
- **Queue Size**: Jobs waiting for execution
- **Success Rate**: Percentage of successful job completions
- **Execution Times**: Average and individual job execution times
- **Retry Statistics**: Number of jobs that required retries

### Performance Monitoring

```python
# Get real-time metrics
pipeline = get_job_pipeline()
metrics = pipeline.get_pipeline_status()

print(f"Success Rate: {metrics['metrics']['success_rate']:.1f}%")
print(f"Jobs per minute: {metrics['metrics']['jobs_per_minute']:.1f}")
```

## Best Practices

### 1. Job Design

- Keep job data lightweight
- Include necessary context in job metadata
- Use appropriate priority levels
- Set reasonable retry limits

### 2. Error Handling

- Implement graceful failure handling in agents
- Log detailed error information
- Use appropriate error messages for user feedback

### 3. Performance

- Monitor queue sizes and processing rates
- Adjust worker pool size based on load
- Use job priorities to manage critical tasks

### 4. Debugging

- Use job tags for categorization
- Monitor execution metrics
- Review failed job patterns

## Testing

### Unit Tests

```bash
# Run pipeline tests
pytest backend/job_pipeline.test.py -v

# Run specific test
pytest backend/job_pipeline.test.py::TestJobPipeline::test_job_execution_success -v
```

### Load Testing

```python
# Example load test
import asyncio

async def load_test():
    pipeline = get_job_pipeline()
    
    # Submit 100 jobs
    for i in range(100):
        await pipeline.submit_job(
            job_id=f"load-test-{i}",
            user_id="load-test-user",
            agent_name="text_processing",
            job_data={"text": f"Test job {i}"}
        )
    
    # Monitor completion
    while True:
        status = pipeline.get_pipeline_status()
        if status['queue_size'] == 0 and status['active_jobs'] == 0:
            break
        await asyncio.sleep(1)
    
    print("Load test completed")
```

## Troubleshooting

### Common Issues

#### 1. Jobs Stuck in Queue
- Check worker status: `GET /pipeline/status`
- Verify agent availability
- Check system resources

#### 2. High Failure Rates
- Review agent error logs
- Check database connectivity
- Validate job data format

#### 3. Slow Processing
- Monitor execution times
- Increase worker pool size
- Optimize agent implementations

#### 4. Memory Issues
- Check cleanup worker status
- Monitor job metrics cleanup
- Adjust cleanup interval

### Debug Commands

```bash
# Check pipeline status
curl -X GET "http://localhost:8000/pipeline/status" \
  -H "Authorization: Bearer <token>"

# View recent jobs
curl -X GET "http://localhost:8000/jobs?limit=10" \
  -H "Authorization: Bearer <token>"

# Check logs for errors
grep "ERROR" logs/app.log | tail -20
```

## Security Considerations

- All job endpoints require authentication
- Jobs are isolated by user ID
- Input validation on all job data
- Rate limiting on job submission
- Secure error message handling

## Future Enhancements

- Job dependency management
- Batch job processing
- Advanced scheduling (cron expressions)
- Job result notifications
- Pipeline analytics dashboard
- Multi-tenant job isolation
- Job workflow orchestration 