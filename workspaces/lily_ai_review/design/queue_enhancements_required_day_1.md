# Queue System Enhancements - Day 1 Requirements

## Problem Statement

The current job queue system has a critical flaw: when the server restarts or a worker process crashes, jobs that were in progress remain stuck in the "in_progress" state indefinitely. This leads to:

1. Lost jobs that never complete
2. Poor user experience as requested papers are never delivered
3. Wasted resources as the system attempts to process new jobs while old ones are stuck

## Proposed Solution: Robust Job Recovery Mechanism

We need to implement a comprehensive job recovery system that can detect and recover stalled jobs automatically.

### 1. Database Schema Updates

```sql
-- Add to a migration script
ALTER TABLE saas_job_tracking 
ADD COLUMN last_heartbeat TIMESTAMP WITH TIME ZONE,
ADD COLUMN retry_count INTEGER DEFAULT 0;
```

### 2. Heartbeat Mechanism

The worker will periodically update a "heartbeat" timestamp while processing a job. If this heartbeat isn't updated for a certain period, the job is considered stalled.

```python
# Add to the job tracking service
async def update_job_heartbeat(job_id):
    """Update the heartbeat timestamp for a job to indicate it's still being processed."""
    try:
        query = """
        UPDATE saas_job_tracking 
        SET last_heartbeat = NOW() 
        WHERE job_id = $1
        """
        await supabase_client.rpc('execute_sql', {'sql_query': query, 'params': [job_id]})
        logger.debug(f"Updated heartbeat for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to update heartbeat for job {job_id}: {str(e)}")
```

### 3. Job Recovery Function

This function will identify and recover stalled jobs:

```python
# Add to queue_manager.py
async def recover_stalled_jobs(max_stall_time_minutes=30):
    """
    Recover jobs that are marked as in_progress but haven't had a heartbeat update
    for more than max_stall_time_minutes.
    """
    try:
        # Find stalled jobs
        stalled_jobs_query = """
        UPDATE saas_job_tracking 
        SET status = 'queued', 
            progress = 0, 
            progress_message = 'Recovered from stalled state', 
            retry_count = COALESCE(retry_count, 0) + 1
        WHERE status = 'in_progress' 
        AND (last_heartbeat IS NULL OR last_heartbeat < NOW() - INTERVAL '%s minutes')
        RETURNING job_id, job_type, retry_count
        """
        
        result = await supabase_client.rpc('execute_sql', {
            'sql_query': stalled_jobs_query, 
            'params': [max_stall_time_minutes]
        })
        
        recovered_jobs = result.data if result.data else []
        
        if recovered_jobs:
            for job in recovered_jobs:
                job_id, job_type, retry_count = job
                logger.warning(f"Recovered stalled job {job_id} of type {job_type} (retry #{retry_count})")
                
            logger.info(f"Recovered {len(recovered_jobs)} stalled jobs")
            
        return len(recovered_jobs)
        
    except Exception as e:
        logger.error(f"Error recovering stalled jobs: {str(e)}")
        return 0
```

### 4. Maximum Retry Limit

To prevent jobs from being retried indefinitely:

```python
# In queue_manager.py
MAX_RETRY_COUNT = 3  # Maximum number of times to retry a job

async def handle_max_retries():
    """Mark jobs that have exceeded the maximum retry count as failed."""
    try:
        max_retries_query = """
        UPDATE saas_job_tracking 
        SET status = 'failed', 
            progress_message = 'Failed after maximum retry attempts'
        WHERE status = 'queued' 
        AND retry_count >= $1
        RETURNING job_id, job_type
        """
        
        result = await supabase_client.rpc('execute_sql', {
            'sql_query': max_retries_query, 
            'params': [MAX_RETRY_COUNT]
        })
        
        failed_jobs = result.data if result.data else []
        
        if failed_jobs:
            for job in failed_jobs:
                job_id, job_type = job
                logger.error(f"Job {job_id} of type {job_type} failed after {MAX_RETRY_COUNT} retry attempts")
                
            logger.info(f"Marked {len(failed_jobs)} jobs as failed due to exceeding retry limit")
            
        return len(failed_jobs)
    except Exception as e:
        logger.error(f"Error handling max retries: {str(e)}")
        return 0
```

### 5. Integration with Worker Process

Update the worker process to include heartbeats and recovery:

```python
# In worker.py
async def process_job(job):
    job_id = job['job_id']
    
    try:
        # Update status to in_progress
        await queue_manager.update_job_status(job_id, 'in_progress')
        
        # Start a background task for heartbeats
        heartbeat_task = asyncio.create_task(heartbeat_loop(job_id))
        
        # Process the job...
        result = await actual_job_processing(job)
        
        # Cancel the heartbeat task
        heartbeat_task.cancel()
        
        # Update final status
        await queue_manager.update_job_status(job_id, 'completed')
        
        return result
        
    except Exception as e:
        # Cancel the heartbeat task if it exists
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            
        # Update status to failed
        await queue_manager.update_job_status(job_id, 'failed', error_message=str(e))
        raise

async def heartbeat_loop(job_id):
    """Send regular heartbeats while the job is being processed."""
    try:
        while True:
            await update_job_heartbeat(job_id)
            await asyncio.sleep(30)  # Update heartbeat every 30 seconds
    except asyncio.CancelledError:
        # Task was cancelled, which is expected when job completes
        pass
    except Exception as e:
        logger.error(f"Error in heartbeat loop for job {job_id}: {str(e)}")
```

### 6. Worker Initialization and Periodic Checks

```python
# In worker_launcher.py
async def initialize_worker():
    # ... existing initialization code ...
    
    # Recover any stalled jobs on startup
    recovered_count = await queue_manager.recover_stalled_jobs()
    logger.info(f"Recovered {recovered_count} stalled jobs on startup")
    
    # Handle jobs that have exceeded retry limits
    failed_count = await queue_manager.handle_max_retries()
    if failed_count > 0:
        logger.info(f"Marked {failed_count} jobs as failed due to exceeding retry limit")
    
    # ... rest of initialization ...

# In the main worker loop
async def worker_loop():
    while True:
        # Process jobs...
        
        # Every 5 minutes, check for stalled jobs and handle max retries
        current_minute = datetime.now().minute
        if current_minute % 5 == 0:
            await queue_manager.recover_stalled_jobs()
            await queue_manager.handle_max_retries()
        
        await asyncio.sleep(poll_interval)
```

## Implementation Priority

1. **Database Schema Updates** - Add the necessary columns to track heartbeats and retry counts
2. **Job Recovery Function** - Implement the function to detect and recover stalled jobs
3. **Heartbeat Mechanism** - Add heartbeat updates to the job processing workflow
4. **Worker Integration** - Update the worker to use the heartbeat and recovery mechanisms
5. **Testing** - Verify that jobs are properly recovered after simulated crashes

## Expected Benefits

1. **Resilience** - Jobs will automatically recover after server restarts or worker crashes
2. **Visibility** - Clear tracking of job retries and failures
3. **Resource Efficiency** - No wasted resources on permanently stalled jobs
4. **Improved User Experience** - Users will reliably receive their requested papers

## Future Enhancements (Post Day-1)

1. **Job Prioritization** - Prioritize recovered jobs to ensure they complete quickly
2. **Notification System** - Alert administrators about jobs that fail after maximum retries
3. **Retry Backoff** - Implement exponential backoff for retried jobs
4. **Job Dependencies** - Allow jobs to depend on other jobs, with proper handling of failures
5. **Job Archiving** - Automatically archive old completed or failed jobs
