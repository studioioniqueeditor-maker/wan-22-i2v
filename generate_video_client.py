import requests
import base64
import time
import os
from video_client_interface import IVideoClient

class WanVideoClient(IVideoClient):
    def __init__(self, runpod_endpoint_id, runpod_api_key):
        self.endpoint_id = runpod_endpoint_id
        self.api_key = runpod_api_key
        self.url = f"https://api.runpod.ai/v2/{self.endpoint_id}/run"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def create_video_from_image(self, image_path, prompt, negative_prompt="", width=1280, height=720, length=121, steps=30, seed=42, cfg=3.0, **kwargs):
        print(f"Encoding image: {image_path}")
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            return {"status": "FAILED", "error": f"Image file not found: {image_path}"}

        payload = {
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "image_base64": image_base64,
                "width": width,
                "height": height,
                "num_frames": length,
                "num_steps": steps,
                "seed": seed,
                "guidance_scale": cfg
            }
        }

        print(f"Sending request to RunPod: {self.url}")
        try:
            submission_time = time.time()
            # Increased timeout for video generation
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=600)
            
            if response.status_code != 200:
                return {
                    "status": "FAILED", 
                    "error": f"API returned status {response.status_code}", 
                    "details": response.text
                }
            
            data = response.json()
            
            # Check for immediate completion or error
            if "error" in data:
                return {"status": "FAILED", "error": data['error']}
            
            if "output" in data:
                completion_time = time.time()
                metrics = {
                    "submission_time": submission_time,
                    "start_time": submission_time, # Started immediately
                    "completion_time": completion_time,
                    "spin_up_time": 0,
                    "generation_time": completion_time - submission_time
                }
                return self._process_output(data, metrics)
            
            # If status is not COMPLETED (e.g. IN_QUEUE, IN_PROGRESS), start polling
            job_id = data.get("id")
            status = data.get("status")
            
            if job_id and status in ["IN_QUEUE", "IN_PROGRESS"]:
                print(f"Job {job_id} is {status}. Polling for completion...")
                return self._poll_job(job_id, submission_time)
            
            return {"status": status, "id": job_id}

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}

    def _poll_job(self, job_id, submission_time, timeout=600, interval=5):
        """Polls the status endpoint until completion or timeout."""
        status_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/status/{job_id}"
        
        start_time = None # Time when status became IN_PROGRESS
        polling_start = time.time()
        
        while time.time() - polling_start < timeout:
            try:
                response = requests.get(status_url, headers=self.headers)
                if response.status_code != 200:
                    print(f"Polling failed: {response.status_code}")
                    time.sleep(interval)
                    continue
                
                data = response.json()
                status = data.get("status")
                
                if status == "IN_PROGRESS" and start_time is None:
                    start_time = time.time()
                
                if status == "COMPLETED":
                    completion_time = time.time()
                    
                    # If we missed the transition to IN_PROGRESS (e.g. very fast job), assume it started just before finishing or use submission time if logic dictates.
                    # For metrics consistency:
                    if start_time is None:
                        start_time = submission_time 
                        
                    spin_up_time = start_time - submission_time
                    generation_time = completion_time - start_time
                    
                    metrics = {
                        "submission_time": submission_time,
                        "start_time": start_time,
                        "completion_time": completion_time,
                        "spin_up_time": spin_up_time,
                        "generation_time": generation_time
                    }
                    return self._process_output(data, metrics)
                elif status == "FAILED":
                    return {"status": "FAILED", "error": data.get("error", "Unknown job error")}
                
                print(f"Status: {status}...")
                time.sleep(interval)
                
            except Exception as e:
                print(f"Polling exception: {e}")
                time.sleep(interval)
                
        return {"status": "FAILED", "error": "Polling timed out"}

    def _process_output(self, data, metrics=None):
        output = data.get("output")
        if isinstance(output, dict) and "error" in output:
             return {"status": "FAILED", "error": output["error"]}
        
        result = {"status": "COMPLETED", "output": output}
        if metrics:
            result["metrics"] = metrics
        return result

    def save_video_result(self, result, output_path):
        if result.get("status") != "COMPLETED":
            print("Cannot save result: Status is not COMPLETED")
            return False

        output_data = result.get("output")
        
        # Robustly handle different output formats
        video_base64 = None
        
        # Handle list output (sometimes RunPod returns a list)
        if isinstance(output_data, list) and len(output_data) > 0:
            output_data = output_data[0]
            
        if isinstance(output_data, dict):
            video_base64 = output_data.get("video_base64") or output_data.get("video")
        elif isinstance(output_data, str):
            video_base64 = output_data

        if not video_base64:
             print(f"Error: No video data found in output. Output type: {type(output_data)}")
             if isinstance(output_data, dict):
                 print(f"Available keys: {list(output_data.keys())}")
             return False

        print(f"Saving video to {output_path}...")
        try:
            # Strip potential data URL prefix
            if isinstance(video_base64, str) and "," in video_base64:
                video_base64 = video_base64.split(",")[1]
                
            video_bytes = base64.b64decode(video_base64)
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            print("Video saved successfully.")
            return True
        except Exception as e:
            print(f"Failed to save video: {e}")
            return False

    def batch_process_images(self, image_folder_path, output_folder_path, prompt, negative_prompt="", width=1280, height=720, length=121, steps=30, seed=42, cfg=3.0):
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
            print(f"Created output directory: {output_folder_path}")

        image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        try:
            files = [f for f in os.listdir(image_folder_path) if f.lower().endswith(image_extensions)]
        except FileNotFoundError:
            print(f"Error: Input directory '{image_folder_path}' not found.")
            return {"successful": 0, "total_files": 0, "results": []}

        total_files = len(files)
        successful = 0
        results = []

        print(f"Found {total_files} images to process in {image_folder_path}")

        for i, filename in enumerate(files, 1):
            print(f"[{i}/{total_files}] Processing {filename}...")
            image_path = os.path.join(image_folder_path, filename)
            output_filename = os.path.splitext(filename)[0] + ".mp4"
            output_path = os.path.join(output_folder_path, output_filename)
            
            result = self.create_video_from_image(
                image_path=image_path,
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                length=length,
                steps=steps,
                seed=seed,
                cfg=cfg
            )
            
            if result.get("status") == "COMPLETED":
                if self.save_video_result(result, output_path):
                    print(f"Successfully processed and saved: {output_filename}")
                    successful += 1
                    results.append({"file": filename, "status": "SUCCESS", "output": output_path})
                else:
                    print(f"Failed to save video for: {filename}")
                    results.append({"file": filename, "status": "SAVE_FAILED"})
            else:
                print(f"Failed to process {filename}: {result.get('error')}")
                results.append({"file": filename, "status": "FAILED", "error": result.get("error")})

        return {
            "total_files": total_files,
            "successful": successful,
            "results": results
        }
