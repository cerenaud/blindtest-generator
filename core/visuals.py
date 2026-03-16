from PIL import Image, ImageDraw, ImageFont

def make_excerpt_frame(countdown_value, track_number, total):
    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))

    draw = ImageDraw.Draw(img)
    draw.text((640, 50), f"Extrait {track_number} / {total}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 40),anchor="mm" )
    draw.text((640, 360), f"{countdown_value}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 150), anchor="mm")

    return img

def get_font_size(draw, text, max_width, font_path, start_size):
    size = start_size
    font = ImageFont.truetype(font_path, size)
    while draw.textlength(text, font=font) > max_width and size > 10:
        size -= 2
        font = ImageFont.truetype(font_path, size)
    return font

def make_reveal_frame(artist: str, title: str):
    img = Image.new("RGB", (1280, 720), color=(10, 10, 50))

    draw = ImageDraw.Draw(img)

    draw.rectangle([(140, 50), (1140, 500)], fill=(30, 30, 30))
    draw.text((640, 250), "?", fill=(100, 100, 100), font=ImageFont.truetype("arial.ttf", 200), anchor="mm")

    # draw.text((640, 570), f"{artist} - {title}", fill=(255, 255, 255),
    #           font=ImageFont.truetype("arial.ttf", 65), anchor="mm")

    text = f"{artist} - {title}"
    font = get_font_size(draw, text, 1000, "arial.ttf", 65)  # max_width = 1000px
    draw.text((640, 570), text, fill=(255, 255, 255), font=font, anchor="mm")

    return img
