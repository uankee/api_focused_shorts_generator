import os
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    ColorClip, ImageClip
)
import numpy as np


class MoviePyRenderer:

    SHORT_WIDTH = 1080
    SHORT_HEIGHT = 1920

    def __init__(self, output_dir: str = "ready_shorts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def render_video(
        self,
        input_video_path: str,
        music_path: str,
        text_image: ImageClip,
        output_path: str  
    ) -> Path:
        video_clip = None
        audio_clip = None
        music_clip = None
        final_clip = None

        try:
            print("[Рендерер] Завантаження вхідного відео...")
            video_clip = VideoFileClip(input_video_path)

            print("[Рендерер] Компонування кадру (1080x1920)...")
            centered_video = self._scale_and_center_video(video_clip)

            background = ColorClip(
                size=(self.SHORT_WIDTH, self.SHORT_HEIGHT),
                color=(0, 0, 0)
            ).set_duration(centered_video.duration)

            text_image = text_image.set_duration(centered_video.duration)

            centered_video_w, centered_video_h = centered_video.size
            scale = self.SHORT_WIDTH / centered_video_w if centered_video_w > 0 else 1
            final_video_h = centered_video_h
            video_y_offset = (self.SHORT_HEIGHT - final_video_h) // 2

            text_y = ((video_y_offset - text_image.h) // 2)
            if text_y < 10:
                text_y = 120

            text_image = text_image.set_position(("center", text_y))

            composite = CompositeVideoClip([
                background,
                centered_video,
                text_image
            ])
            composite = composite.set_duration(centered_video.duration)
            print("[Рендерер] Обробка аудіо з керуванням гучністю...")
            audio_composite = self._create_audio_mix(
                video_clip, music_path, centered_video.duration
            )
            final_clip = composite.set_audio(audio_composite)

            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            print(f"[Рендерер] Запис результату: {output_path_obj}")

            final_clip.write_videofile(
                str(output_path_obj),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            print(f"[Рендерер] ✓ Відео відрендеровано: {output_path_obj}")
            return output_path_obj

        finally:
            self._cleanup_clips([video_clip, audio_clip, music_clip, final_clip])

    def _scale_and_center_video(self, video_clip: VideoFileClip) -> VideoFileClip:
        original_w, original_h = video_clip.size
        aspect_ratio = original_h / original_w

        if aspect_ratio > 1.2:
            print(f"[Рендерер] Виявлено вертикальне відео (aspect ratio: {aspect_ratio:.2f})")
            print(f"[Рендерер] Автоматичний кропінг до формату близько 1:1...")

            crop_height = int(original_h * 0.65)
            crop_top = (original_h - crop_height) // 2
            crop_bottom = crop_top + crop_height

            cropped = video_clip.crop(x1=0, y1=crop_top, x2=original_w, y2=crop_bottom)
            print(f"[Рендерер] Обрізано з {original_h}px до {crop_height}px висоти")

            video_clip = cropped
            original_h = crop_height

        scale = self.SHORT_WIDTH / original_w
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        resized = video_clip.resize((new_w, new_h))

        y_offset = (self.SHORT_HEIGHT - new_h) // 2

        print(f"[Рендерер] Масштабування: {new_w}x{new_h}, вертикальний зсув: {y_offset}px")

        positioned = resized.set_position(("center", y_offset))
        return positioned

    def _create_audio_mix(
        self, video_clip: VideoFileClip, music_path: str, duration: float
    ) -> CompositeAudioClip:
        from moviepy.audio.fx.all import audio_loop
        audio_clips = []

        if video_clip.audio is not None:
            original_audio_ducked = video_clip.audio.volumex(0.1)
            audio_clips.append(original_audio_ducked)

        music_clip = AudioFileClip(music_path)

        if music_clip.duration < duration:
            music_clip = audio_loop(music_clip, duration=duration)
        else:
            music_clip = music_clip.subclip(0, duration)

        music_with_volume = music_clip.volumex(0.95)
        audio_clips.append(music_with_volume)

        return CompositeAudioClip(audio_clips)

    def _get_output_path(self, filename: str = None) -> Path:
        if filename is None:
            import time
            timestamp = int(time.time())
            filename = f"short_{timestamp}.mp4"

        return self.output_dir / filename

    @staticmethod
    def _cleanup_clips(clips: list):
        for clip in clips:
            if clip is not None:
                try:
                    clip.close()
                except Exception as e:
                    print(f"[Попередження] Помилка закриття кліпу: {e}")