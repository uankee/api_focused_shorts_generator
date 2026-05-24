from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip
import numpy as np
import random
from pathlib import Path


class TextHighlightRenderer:
    IMG_WIDTH = 1000
    IMG_HEIGHT = 300  
    PADDING = 20
    LINE_SPACING = 65 

    FONT_SIZE = 70 
    FONT_COLOR_MAIN = (255, 255, 255) 
    HIGHLIGHT_COLORS = [
        (255, 0, 0),      # червоний
        (0, 255, 0),      # зелений
        (255, 255, 0),    # жовтий
        (255, 165, 0),    # оранжевий
        (255, 192, 203),  # рожевий
    ]

    def __init__(self, font_path: str = None):
        self.font_path = font_path or self._find_font()
        try:
            self.font = ImageFont.truetype(self.font_path, self.FONT_SIZE)
        except Exception as e:
            print(f"[Попередження] Не вдалося завантажити шрифт {self.font_path}: {e}")
            self.font = ImageFont.load_default()

    def render_text_image(
        self, main_text: str, highlights: list, duration: float = 5.0
    ) -> ImageClip:
        img = Image.new("RGBA", (self.IMG_WIDTH, self.IMG_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        lines = self._wrap_text(main_text, draw)

        y_offset = self.PADDING
        for line in lines:
            self._draw_line_with_highlights(draw, line, highlights, y_offset)
            y_offset += self.LINE_SPACING

        img_np = np.array(img)
        
        rgb_array = img_np[:, :, :3]
        alpha_array = img_np[:, :, 3] / 255.0
        
        image_clip = ImageClip(rgb_array)
        mask_clip = ImageClip(alpha_array, ismask=True)
        image_clip = image_clip.set_mask(mask_clip)

        image_clip = image_clip.set_position(("center", 50)).set_duration(duration)

        return image_clip

    def _wrap_text(self, text: str, draw: ImageDraw.ImageDraw) -> list:
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=self.font)
            text_width = bbox[2] - bbox[0]

            if text_width <= (self.IMG_WIDTH - 2 * self.PADDING):
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _draw_line_with_highlights(
        self,
        draw: ImageDraw.ImageDraw,
        line: str,
        highlights: list,
        y_offset: int
    ):
        words = line.split()
        
        total_width = 0
        for word in words:
            bbox = draw.textbbox((0, 0), word, font=self.font)
            total_width += bbox[2] - bbox[0]
        
        if words:
            space_bbox = draw.textbbox((0, 0), " ", font=self.font)
            space_w = space_bbox[2] - space_bbox[0]
            total_width += space_w * (len(words) - 1)

        x_offset = (self.IMG_WIDTH - total_width) // 2

        for word in words:
            clean_word = word.lower().strip(".,!?\"'()«»:-")
            
            matched_idx = -1
            if clean_word:
                for i, h in enumerate(highlights):
                    h_words = [hw.lower().strip(".,!?\"'()«»:-") for hw in h.split()]
                    if clean_word in h_words:
                        matched_idx = i 
                        break

            if matched_idx != -1:
                color = self.HIGHLIGHT_COLORS[matched_idx % len(self.HIGHLIGHT_COLORS)]
            else:
                color = self.FONT_COLOR_MAIN
            draw.text((x_offset, y_offset), word, font=self.font, fill=color + (255,))

            bbox = draw.textbbox((0, 0), word + " ", font=self.font)
            x_offset += bbox[2] - bbox[0]
    @staticmethod
    def _find_font() -> str:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Impact.ttf",  # macOS
            "C:\\Windows\\Fonts\\impact.ttf",   # Windows 
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",  # Linux alt
        ]

        for font_path in font_paths:
            if Path(font_path).exists():
                print(f"[TextRenderer] Використання шрифту: {font_path}")
                return font_path

        print("[TextRenderer] Системний шрифт не знайдено, використання типового")
        return None


def format_text_with_highlights(main_text: str, highlights: list, duration: float = 5.0):
    renderer = TextHighlightRenderer()
    
    fresh_colors = [
        (255, 215, 0),   # жовтий
        (50, 205, 50),   # зелений
        (255, 69, 0),    # оранжево-червоний
        (0, 255, 255),   # циан
        (255, 105, 180)  # рожевий
    ]
    
    if hasattr(renderer, 'colors'):
        renderer.colors = fresh_colors.copy()
    elif hasattr(renderer, 'HIGHLIGHT_COLORS'):
        renderer.HIGHLIGHT_COLORS = fresh_colors.copy()
        
    return renderer.render_text_image(main_text, highlights, duration)