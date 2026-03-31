import os
import time
import json
from google import genai

class VideoAnalyzer:
    def __init__(self, api_key, logger_callback):
        self.api_key = api_key
        self.log = logger_callback

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def analyze_with_gemini(self, video_path, action_description):
        if not self.client:
            self.log("[AI ERROR] Gemini API Key is missing! Set it in Settings.")
            return None

        self.log(f"[AI] Uploading {os.path.basename(video_path)} to Gemini for analysis...")
        try:
            # 1. Upload the video file to Gemini
            video_file = self.client.files.upload(file=video_path)

            # 2. Wait for Gemini to finish processing the video
            self.log("[AI] Video uploaded. Waiting for Gemini to process the file...")
            while video_file.state.name == "PROCESSING":
                time.sleep(3)  # Check every 3 seconds
                # Refresh the file status
                video_file = self.client.files.get(name=video_file.name)

            if video_file.state.name == "FAILED":
                self.log("[AI ERROR] Gemini failed to process this video.")
                return None

            # 3. Prompt Gemini to find the exact action
            prompt = f"""
                    Watch this video carefully. The user is looking for clips showing exactly this action/concept: "{action_description}"

                    Find the exact start and end timestamps (in seconds) where this action is actively happening on screen.
                    Ignore any parts where a person is just talking to the camera about the action.

                    Return ONLY a valid JSON list of dictionaries containing 'start' and 'end' float values. 
                    Example format:
                    [
                        {{"start": 12.5, "end": 18.0}},
                        {{"start": 45.0, "end": 52.5}}
                    ]
                    If the action does not occur in the video, return an empty list: []
                    """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[video_file, prompt],
                config={"response_mime_type": "application/json"}
            )

            # 4. Clean up: Delete the file from Gemini's servers to save your quota
            self.client.files.delete(name=video_file.name)

            # 5. Parse the JSON response
            try:
                clips = json.loads(response.text)
            except json.JSONDecodeError:
                self.log("[AI ERROR] Gemini returned invalid JSON format.")
                self.log(response.text)
                return None

            if not clips:
                return None

            # Convert JSON dicts into a list of tuples: [(start, end), (start, end)]
            final_clips = []
            for i, clip in enumerate(clips):
                start = float(clip.get("start", 0.0))
                end = float(clip.get("end", 0.0))

                # Only keep clips that are at least 1 second long
                if end - start >= 1.0:
                    final_clips.append((start, end))
                    self.log(f"      -> AI Found Action: {start}s to {end}s")

            return final_clips if final_clips else None
        except Exception as e:
            self.log(f"[AI ERROR] {str(e)}")
            return None
