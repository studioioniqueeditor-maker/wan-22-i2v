from abc import ABC, abstractmethod

class IVideoClient(ABC):
    @abstractmethod
    def create_video_from_image(self, image_path, prompt, **kwargs):
        """
        Initiates video generation.
        Returns a dictionary with status, job_id, or output/error.
        """
        pass

    @abstractmethod
    def save_video_result(self, result, output_path):
        """
        Saves the video result to the specified path.
        Returns True on success, False otherwise.
        """
        pass
