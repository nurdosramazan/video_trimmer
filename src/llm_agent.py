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
    
            Task 1: Create a highly optimized, broad search query for YouTube to find this action.
            Task 2: List 2 to 4 specific, physical objects that MUST appear on screen for this action to occur.
            Task 3: List 3 to 5 broad category synonyms for those objects (e.g., if object is 'onion', synonym is 'vegetable' or 'food'). Google Cloud Vision uses broad labels, so these are crucial.
            Task 4: List 2 to 4 negative visual concepts that indicate the person is just talking to the camera instead of doing the action (e.g., 'face', 'portrait', 'conversation', 'speaking').

            Return ONLY valid JSON:
            {{
                "platform_search_query": "string",
                "vision_target_objects": ["obj1", "obj2"],
                "broad_synonyms": ["synonym1", "synonym2"],
                "negative_concepts": ["neg1", "neg2"]
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
