from PIL import Image, ImageDraw, ImageFont

def make_excerpt_frame(countdown_value, track_number, total):
    img = Image.new("RGB", (1280, 720), color=(0, 0, 0))

    draw = ImageDraw.Draw(img)
    draw.text((640, 50), f"Extrait {track_number} / {total}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 40),anchor="mm" )
    draw.text((640, 360), f"{countdown_value}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 150), anchor="mm")

    return img

def make_reveal_frame(artist: str, title: str):
    img = Image.new("RGB", (1280, 720), color=(10, 10, 50))

    draw = ImageDraw.Draw(img)

    draw.rectangle([(140, 50), (1140, 500)], fill=(30, 30, 30))
    draw.text((640, 250), "?", fill=(100, 100, 100), font=ImageFont.truetype("arial.ttf", 200), anchor="mm")

    draw.text((640, 570), f"{artist} - {title}", fill=(255, 255, 255),
              font=ImageFont.truetype("arial.ttf", 65), anchor="mm")

    return img
