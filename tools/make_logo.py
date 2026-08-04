from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 512
OUT = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

TERMINAL_BG = (24, 25, 33)
TERMINAL_BORDER = (52, 56, 68)
TITLE = (160, 165, 180)
PROMPT = (84, 224, 152)
LINKEDIN = (10, 102, 194)
LINKEDIN_TEXT = (255, 255, 255)
CURSOR = (84, 224, 152)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill,
    outline=None,
    width=1,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def main() -> None:
    img = Image.new("RGB", (SIZE, SIZE), TERMINAL_BG)
    draw = ImageDraw.Draw(img)

    margin = 28
    rounded_rect(
        draw,
        (margin, margin, SIZE - margin, SIZE - margin),
        26,
        fill=TERMINAL_BG,
        outline=TERMINAL_BORDER,
        width=3,
    )

    title_font = ImageFont.truetype(MONO, 30)
    dot_size = 14
    dots = [(60, 64), (92, 64), (124, 64)]
    dot_colors = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]
    for (cx, cy), color in zip(dots, dot_colors):
        draw.ellipse(
            (cx - dot_size / 2, cy - dot_size / 2, cx + dot_size / 2, cy + dot_size / 2), fill=color
        )

    title_text = "linkedin-cli"
    tw = draw.textlength(title_text, font=title_font)
    draw.text(
        ((SIZE - tw) / 2, 64 - title_font.size / 2 - 4), title_text, font=title_font, fill=TITLE
    )

    draw.line((margin + 24, 112, SIZE - margin - 24, 112), fill=TERMINAL_BORDER, width=2)

    prompt_font = ImageFont.truetype(MONO_BOLD, 84)
    in_font = ImageFont.truetype(SANS_BOLD, 110)

    prompt_text = "$"
    prompt_w = draw.textlength(prompt_text, font=prompt_font)
    prompt_x = 64
    prompt_y = 200
    draw.text((prompt_x, prompt_y), prompt_text, font=prompt_font, fill=PROMPT)

    box_x = prompt_x + prompt_w + 28
    box_size = 168
    box_y = prompt_y - 8
    rounded_rect(draw, (box_x, box_y, box_x + box_size, box_y + box_size), 42, fill=LINKEDIN)

    in_w = draw.textlength("in", font=in_font)
    draw.text(
        (box_x + (box_size - in_w) / 2, box_y + (box_size - in_font.size) / 2),
        "in",
        font=in_font,
        fill=LINKEDIN_TEXT,
    )

    cursor_x = box_x + box_size + 30
    draw.rectangle((cursor_x, prompt_y + 6, cursor_x + 34, prompt_y + 6 + 84), fill=CURSOR)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"written: {OUT} ({img.size})")


if __name__ == "__main__":
    main()
