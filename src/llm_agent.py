from google import genai
import json

class LLMAgent:
    def __init__(self, api_key, logger_callback):
        self.api_key = api_key
        self.log = logger_callback
        self.client = genai.Client(api_key=api_key)

    def translate_intent(self, raw_input):
        if not self.api_key:
            self.log("[AGENT ERROR] Gemini API Key is missing! Set it in Settings.")
            return None

        try:
            prompt = f"""
            A user wants to find video clips of the following action/concept: "{raw_input}"
    
            Task 1: Create a highly optimized, broad search query to type into YouTube to find videos likely to contain this action.
            Task 2: Break this action down into a list of 2 to 5 specific, physical visual nouns (objects) that must appear in the camera frame for this action to be happening.
    
            Return ONLY valid JSON in this exact format:
            {{
                "platform_search_query": "string",
                "vision_target_objects": ["noun1", "noun2", "noun3"]
            }}
            """

            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )

            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                self.log("[AGENT ERROR] Invalid JSON returned from model")
                self.log(response.text)
                return None

            self.log(f"[AGENT] Optimized Search Query: '{result['platform_search_query']}'")
            self.log(f"[AGENT] Target Visual Objects: {', '.join(result['vision_target_objects'])}")
            return result
        except Exception as e:
            self.log(f"[AGENT ERROR] Failed to parse intent: {str(e)}")
            return None
