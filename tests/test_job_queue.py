"""
Tests for the Job Queue System
"""
import pytest
import tempfile
import os
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

from job_queue import JobQueue, JobStatus, Job

class TestJobQueue:
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        try:
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.fixture
    def queue(self, temp_db):
        """Create a job queue instance with temporary database."""
        queue = JobQueue(db_path=temp_db)
        yield queue
        queue.stop_worker()

    def test_singleton_pattern(self):
        """Test that JobQueue uses singleton pattern."""
        q1 = JobQueue.get_instance()
        q2 = JobQueue.get_instance()
        assert q1 is q2

    def test_add_job(self, queue):
        """Test adding a job to the queue."""
        job_data = {
            "user_id": "user123",
            "model": "wan2.1",
            "prompt": "Test prompt",
            "input_image_path": "/tmp/test.jpg",
            "parameters": {"cfg": 7.5}
        }
        
        job_id = queue.add_job(job_data)
        assert job_id is not None
        assert isinstance(job_id, str)
        
        # Verify job exists
        job = queue.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.user_id == "user123"
        assert job.status == JobStatus.QUEUED

    def test_get_job(self, queue):
        """Test retrieving a job."""
        job_data = {
            "user_id": "user123",
            "model": "veo3.1",
            "prompt": "Test",
            "input_image_path": "/tmp/test.jpg"
        }
        
        job_id = queue.add_job(job_data)
        job = queue.get_job(job_id)
        
        assert job is not None
        assert job.job_id == job_id
        assert job.model == "veo3.1"

    def test_cancel_job(self, queue):
        """Test cancelling a queued job."""
        job_data = {
            "user_id": "user123",
            "model": "wan2.1",
            "prompt": "Test",
            "input_image_path": "/tmp/test.jpg"
        }
        
        job_id = queue.add_job(job_data)
        
        # Should be able to cancel queued job
        assert queue.cancel_job(job_id) is True
        
        job = queue.get_job(job_id)
        assert job.status == JobStatus.CANCELLED

    def test_cancel_non_queued_job(self, queue):
        """Test that only queued jobs can be cancelled."""
        job_data = {
            "user_id": "user123",
            "model": "wan2.1",
            "prompt": "Test",
            "input_image_path": "/tmp/test.jpg"
        }
        
        job_id = queue.add_job(job_data)
        
        # Manually set to processing
        job = queue.get_job(job_id)
        job.status = JobStatus.PROCESSING
        queue._save_job(job)
        
        # Should not be able to cancel
        assert queue.cancel_job(job_id) is False

    def test_get_user_jobs(self, queue):
        """Test retrieving user's job history."""
        # Add multiple jobs for different users
        for i in range(3):
            queue.add_job({
                "user_id": "user1",
                "model": "wan2.1",
                "prompt": f"Test {i}",
                "input_image_path": "/tmp/test.jpg"
            })
        
        queue.add_job({
            "user_id": "user2",
            "model": "veo3.1",
            "prompt": "Other user",
            "input_image_path": "/tmp/test.jpg"
        })
        
        user1_jobs = queue.get_user_jobs("user1", limit=10)
        assert len(user1_jobs) == 3
        
        user2_jobs = queue.get_user_jobs("user2", limit=10)
        assert len(user2_jobs) == 1

    def test_job_to_dict(self):
        """Test Job serialization."""
        job = Job(
            job_id="test123",
            user_id="user123",
            model="wan2.1",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            prompt="Test prompt",
            result_url="https://example.com/video.mp4"
        )
        
        job_dict = job.to_dict()
        assert job_dict["job_id"] == "test123"
        assert job_dict["status"] == "completed"
        assert job_dict["prompt"] == "Test prompt"

    @patch('job_queue.VideoClientFactory')
    def test_process_job_success(self, mock_factory, queue):
        """Test successful job processing."""
        # Mock video client
        mock_client = MagicMock()
        mock_client.create_video_from_image.return_value = {
            "status": "COMPLETED",
            "output": b"fake_video_data"
        }
        mock_client.save_video_result.return_value = True
        mock_factory.get_client.return_value = mock_client
        
        # Mock storage service
        with patch('job_queue.StorageService') as mock_storage:
            mock_storage.return_value.upload_file.return_value = "https://example.com/video.mp4"
            
            # Create job
            job_data = {
                "user_id": "user123",
                "model": "wan2.1",
                "prompt": "Test",
                "input_image_path": "/tmp/test.jpg",
                "parameters": {"cfg": 7.5}
            }
            
            job_id = queue.add_job(job_data)
            job = queue.get_job(job_id)
            
            # Process job
            queue._process_job(job)
            
            # Verify completion
            job = queue.get_job(job_id)
            assert job.status == JobStatus.COMPLETED
            assert job.result_url is not None

    @patch('job_queue.VideoClientFactory')
    def test_process_job_failure(self, mock_factory, queue):
        """Test job processing failure."""
        # Mock video client that fails
        mock_client = MagicMock()
        mock_client.create_video_from_image.return_value = {
            "status": "FAILED",
            "error": "Generation failed"
        }
        mock_factory.get_client.return_value = mock_client
        
        job_data = {
            "user_id": "user123",
            "model": "wan2.1",
            "prompt": "Test",
            "input_image_path": "/tmp/test.jpg"
        }
        
        job_id = queue.add_job(job_data)
        job = queue.get_job(job_id)
        
        queue._process_job(job)
        
        job = queue.get_job(job_id)
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Generation failed"

    def test_worker_starts_new_jobs(self, queue):
        """Test that worker processes queued jobs automatically."""
        # This test would need more complex mocking
        # For now, we verify the worker can be started
        queue.start_worker()
        assert queue.worker_thread is not None
        assert queue.worker_thread.is_alive()

    def test_database_persistence(self, temp_db):
        """Test that jobs persist across queue instances."""
        q1 = JobQueue(db_path=temp_db)
        
        job_id = q1.add_job({
            "user_id": "user123",
            "model": "wan2.1",
            "prompt": "Test",
            "input_image_path": "/tmp/test.jpg"
        })
        
        # Create new instance
        q2 = JobQueue(db_path=temp_db)
        
        # Job should exist
        job = q2.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id

class TestJobStatusEnum:
    def test_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
