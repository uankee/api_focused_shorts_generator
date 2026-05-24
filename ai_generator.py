import json
import time
import google.generativeai as genai


class GeminiAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def upload_video(self, video_path: str) -> str:
        file = genai.upload_file(video_path)
        print(f"[Gemini] Відео завантажено: {file.name}")

        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(file.name)

        if file.state.name != "ACTIVE":
            raise Exception(f"Обробка відео на сервері не вдалася: {file.state.name}")

        print(f"[Gemini] Обробка відео завершена: {file.name}")
        return file.name

    def generate_text(self, video_file_name: str) -> dict:
        system_prompt = self._get_classification_prompt()

        video_file = genai.get_file(video_file_name)
        response = self.model.generate_content(
            [system_prompt, video_file],
            generation_config=genai.types.GenerationConfig(temperature=0.9),
        )

        return self._parse_json_response(response.text)

    @staticmethod
    def _get_classification_prompt() -> str:
        return """You are a master of short-form viral storytelling. Analyze the video and perform these steps:

STEP 1 - CLASSIFICATION (STRICT):
- "Sport": Professional athletic competitions, world records, championships, pure physical performance.
- "Tech": Engineering, machinery, automotive mechanics, physics experiments, industrial innovation.
- "TrueMan": Raw masculine reality. Includes: War, combat/boxing, resilience, fishing, labor, historical leadership, stoicism, self-improvement, and extreme events (high-speed crashes/stunts).

STEP 2 - DYNAMIC COPYWRITING & TEXT LENGTH:
IF SPORT:
  - Act like an elite sports historian and commentator. 
  - If Gemini recognizes a specific historical event, tournament, fight, match, athlete, or world record—name it directly and accurately (e.g., "Tyson vs Holyfield 1997", "UCL Finals").
  - Blend this concrete fact with a massive viral hook. Be highly specific about what is happening in the footage.
  - Length: Can use the maximum character limit to deliver precise facts and context.

IF TECH:
  - Something between Sport and TrueMan. 
  - Do not be overly abstract, but don't just dump raw data either. Focus on "how it works", physics magic, and mechanical beauty.
  - Balance sharp engineering context with a powerful visual hook (e.g., "No electronics. Just pure 1990s mechanics").

IF TRUEMAN:
  - Focus on brutal truth, psychological laws, honor, high-speed adrenaline, or dark motivation.
  - Keep it as it is now: short, punchy, declarative, mature, and uncompromising (minimal text, maximum impact).

STEP 3 - TEXT GENERATION & COLOR HIGHLIGHTS:
- Start with a powerful hook. No filler.
- Max 120 characters total. 1-2 sentences. Lines must be short (4-7 words per line).
- CRITICAL FOR HIGHLIGHTS: You must select MORE words for visual emphasis than usual. Provide at least 4 to 6 high-impact words/phrases that carry the emotional or technical weight of the text.

STEP 4 - RETURN ONLY VALID JSON:
{
  "detected_topic": "Sport" | "Tech" | "TrueMan",
  "main_text": "Your generated viral text (1-2 sentences, max 120 chars)",
  "highlights": ["word1", "word2", "word3", "word4", "word5", "word6"]
}

CRITICAL RULES:
- If the video content is ambiguous, prioritize "TrueMan" if it shows grit, speed, or danger.
- Never include markdown code blocks (```json ... 
```). Just raw JSON string.
- Every highlight must be a powerful word extracted strictly from the generated 'main_text' so the renderer can colorize it properly.
"""

    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(f"У відповіді не знайдено валідну JSON: {response_text}")

        json_str = response_text[json_start:json_end]
        parsed = json.loads(json_str)

        required_fields = ["detected_topic", "main_text", "highlights"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Невірна структура JSON: відсутнє поле '{field}' в {parsed}")

        # Валідуємо detected_topic
        valid_topics = ["Sport", "Tech", "TrueMan"]
        if parsed["detected_topic"] not in valid_topics:
            print(f"[Попередження] Невідома тема: {parsed['detected_topic']}, використовуємо 'Tech'")
            parsed["detected_topic"] = "Tech"

        return parsed

    def cleanup(self, video_file_name: str):
        genai.delete_file(video_file_name)
        print(f"[Gemini] Очищено тимчасові файли: {video_file_name}")
