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
            Create a highly optimized, short search query for platforms like YouTube/TikTok to find this action.

            Return ONLY valid JSON:
            {{
                "platform_search_query": "string"
            }}
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )

            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                self.log("[AGENT ERROR] Invalid JSON returned from model")
                return None

            self.log(f"[AGENT] Optimized Search Query: '{result['platform_search_query']}'")
            return result
        except Exception as e:
            self.log(f"[AGENT ERROR] Failed to parse intent: {str(e)}")
            return None
