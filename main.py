import os
import re
import random
from pathlib import Path
from dotenv import load_dotenv
import yt_dlp

from ai_generator import GeminiAnalyzer
from video_renderer import MoviePyRenderer
from text_formatter import format_text_with_highlights

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

INPUTS_DIR = "inputs"
MUSIC_LIBRARY_DIR = "music_library"
OUTPUT_BASE_DIR = "ready_shorts"


def download_video(url: str) -> str:
    output_dir = Path(INPUTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "%(title)s.%(ext)s"

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': str(output_path),
        'restrictfilenames': True,
        'quiet': False,
        'no_warnings': True,
    }

    print(f"\n[Завантаження] Завантажуємо відео за посиланням: {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    print(f"[Завантаження] ✅ Успішно завантажено: {Path(downloaded_file).name}")
    return downloaded_file


def get_input_videos() -> list:
    video_dir = Path(INPUTS_DIR)
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)
        return []

    videos = sorted(list(video_dir.glob("*.mp4")))
    return [str(v) for v in videos]


def get_random_music() -> str:
    music_dir = Path(MUSIC_LIBRARY_DIR)
    if not music_dir.exists():
        raise FileNotFoundError(f"Директорія не знайдена: {MUSIC_LIBRARY_DIR}")

    tracks = list(music_dir.glob("*.mp3"))
    if not tracks:
        raise FileNotFoundError(f"Файлів .mp3 не знайдено у {MUSIC_LIBRARY_DIR}")

    return str(random.choice(tracks))


def process_video(
    video_path: str,
    analyzer: GeminiAnalyzer,
    renderer: MoviePyRenderer
):
    video_filename = Path(video_path).name
    print(f"\n[Пайплайн] Аналіз та обробка файлу: {video_filename}")

    music_path = get_random_music()
    print(f"[Пайплайн] Вибрана музика: {Path(music_path).name}")

    video_file_name = analyzer.upload_video(video_path)

    try:
        ai_response = analyzer.generate_text(video_file_name)
        
        topic = ai_response["detected_topic"]
        print(f"[Пайплайн] ШІ Авто-Класифікація ТЕМИ: 【{topic}】")
        print(f"[Пайплайн] Генерований текст: {ai_response['main_text']}")
        print(f"[Пайплайн] Ключові слова: {', '.join(ai_response['highlights'])}")

        clean_text = ai_response["main_text"].replace("**", "") 

        text_image = format_text_with_highlights(
            clean_text,
            ai_response["highlights"],
            duration=5.0
)

        output_dir = Path(OUTPUT_BASE_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = video_filename.replace('.mp4', '')
        output_filename = f"{topic}_{original_name}.mp4"
        full_output_path = str(output_dir / output_filename)

        output_path = renderer.render_video(
            video_path,
            music_path,
            text_image,
            full_output_path
        )

        print(f"[Пайплайн] ✅ Ролик успішно створено: {output_path}")

        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"[Пайплайн] 🗑 Очищено оригінальний вхідний файл: {video_filename}")

    finally:
        analyzer.cleanup(video_file_name)


def process_all_videos(analyzer: GeminiAnalyzer, renderer: MoviePyRenderer):
    video_queue = get_input_videos()

    if not video_queue:
        print(f"\n[Пайплайн] ⚠️ Відео для обробки не знайдено у папки {INPUTS_DIR}")
        return

    total_videos = len(video_queue)
    print(f"\n{'='*60}")
    print(f"[Пайплайн] Знайдено {total_videos} відео в черзі на обробку")
    print(f"[Пайплайн] Послідовний ШІ-аналіз та рендеринг запущені...")
    print(f"{'='*60}")

    for index, video_path in enumerate(video_queue, 1):
        print(f"\n[Пайплайн] [{index}/{total_videos}] Запуск процесу...")
        try:
            process_video(video_path, analyzer, renderer)
        except Exception as e:
            print(f"[Пайплайн] ❌ Помилка під час обробки {Path(video_path).name}: {e}")

    print(f"\n{'='*60}")
    print(f"[Пайплайн] Усі відео з черги повністю оброблені!")
    print(f"{'='*60}")


def main():
    if not GEMINI_API_KEY:
        raise ValueError("Відсутній GEMINI_API_KEY у файлі .env")

    Path(INPUTS_DIR).mkdir(exist_ok=True)
    Path(MUSIC_LIBRARY_DIR).mkdir(exist_ok=True)
    Path(OUTPUT_BASE_DIR).mkdir(exist_ok=True)

    if not Path(MUSIC_LIBRARY_DIR).exists() or not list(Path(MUSIC_LIBRARY_DIR).glob("*.mp3")):
        print(f"[Пайплайн]  Директорія музики {MUSIC_LIBRARY_DIR}/ порожня! Додайте туди .mp3")

    print("\n" + "="*60)
    print("="*60)
    print("надішліть посилання на відео для завантаження (можна кілька, по одному в рядку)")
    print("Після вставки напишіть слово START у новому рядку")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'START': 
                break
            lines.append(line)
        except EOFError:
            break
         
    full_text = "\n".join(lines)
    
    urls = re.findall(r'(https?://[^\s^\n^,^\"]+)', full_text)
    
    if not urls:
        print("\n⚠️ У введеному тексті не знайдено жодного валідного посилання.")
        return
        
    print(f"\n[Парсер] Аналіз завершено! Знайдено {len(urls)} лінків у тексті.")
    
    downloaded_count = 0
    for idx, url in enumerate(urls, 1):
        print(f"\n[Черга завантажень] Обробка лінку [{idx}/{len(urls)}]")
        try:
            download_video(url)
            downloaded_count += 1
        except Exception as e:
            print(f"❌ Помилка при завантаженні {url}: {e}")
            
    print(f"\n[Пайплайн] Завантаження завершено. Успішно скачано: {downloaded_count} відео.")
    print("[Пайплайн] Починаємо автоматичний ШІ-аналіз та рендеринг роликів...")
    
    analyzer = GeminiAnalyzer(GEMINI_API_KEY)
    renderer = MoviePyRenderer(OUTPUT_BASE_DIR)

    process_all_videos(analyzer, renderer)


if __name__ == "__main__":
    main()