from PIL import Image, ImageDraw, ImageFont

def make_guessing_frame(
        countdown_value : int,
        track_number : int,
        total : int,
        frame_resolution: tuple[int,int] = (1920,1080)
    ) -> Image.Image :
    """Create an image frame for the guessing part of a blindtest. The image frame displays
    current track number, the total number of tracks in the blindtest and a countdown number.

    Parameters
    ----------
    countdown_value : int
        Number of seconds left in the countdown.
    track_number : int
        Index of the current track in the blindtest.
    total : int
        Total number of tracks in the blindtest.
    frame_resolution : tuple
        Resolution of the image frame. Default is 1920*1080 (1080p standard YouTube)

    Returns
    -------
    Image.Image
        A {frame_resolution} RGB image.
    """

    img= Image.new("RGB", frame_resolution, color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    #Writing index of the track number and the countdown based on frame_resolution
    width, height = frame_resolution
    draw.text((width // 2, height // 20), f"Extrait {track_number} / {total}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 40),anchor="mm" )
    draw.text((width // 2, height // 2), f"{countdown_value}", fill=(255, 255, 255), font=ImageFont.truetype("arial.ttf", 150), anchor="mm")

    return img

def get_font_size(
        draw: ImageDraw.ImageDraw,
        text: str,
        max_width: int,
        font_path: str,
        start_size: int
) -> ImageFont.FreeTypeFont :
    """Find the largest font size that fits the text within a given width.
    Decreases the font size by 2 until the text fits within max_width.

    Parameters
    ----------
    draw : ImageDraw.ImageDraw
        The ImageDraw instance used to measure text length.
    text : str
        The text to fit.
    max_width : int
        Maximum allowed width in pixels.
    font_path : str
        Path to the .ttf font file.
    start_size : int
        Initial font size to start from.

    Returns
    -------
    ImageFont.FreeTypeFont
        The largest font that fits within max_width.
    """
    size = start_size
    font = ImageFont.truetype(font_path, size)
    while draw.textlength(text, font=font) > max_width and size > 10:
        size -= 2
        font = ImageFont.truetype(font_path, size)
    return font

def make_reveal_frame(
        artist: str,
        title: str,
        album_cover_path: str,
        frame_resolution: tuple[int,int] = (1920,1080)
) -> Image.Image :
    """Create an image frame for the reveal part of a blindtest.

    Displays a dark blue background with a placeholder rectangle,
    the artist name and track title centered at the bottom.

    Parameters
    ----------
    artist : str
        Name of the artist.
    title : str
        Title of the track.
    album_cover_path : str
        Path to the album cover image (.jpg).
    frame_resolution : tuple
        Resolution of the image frame. Default is 1920*1080 (1080p standard YouTube)

    Returns
    -------
    Image.Image
        A {frame_resolution} RGB image.
    """
    img = Image.new("RGB", frame_resolution, color=(10, 10, 50))

    draw = ImageDraw.Draw(img)

    #Add a rectangle in which an image of the artist of the song will be included, or a excerpt from a clip
    #TODO
    width, height = frame_resolution
    # draw.rectangle([(int(width * 0.11), int(height * 0.05)), (int(width * 0.89), int(height * 0.70))], fill=(30, 30, 30))
    # draw.text(
    #     (width // 2, height // 3),
    #     "?",
    #     fill=(100, 100, 100),
    #     font=ImageFont.truetype("arial.ttf", int(height * 0.25)),
    #     anchor="mm"
    # )
    #insert album cover
    #album_cover = Image.open("C:/Users/chris/Desktop/Dev/blindtest-generator/data/covers/discovery.jpg")
    album_cover = Image.open(album_cover_path)

    #need to stretch to keep proportion, below is too wide:
    album_cover = album_cover.convert("RGB")

    rect_x1, rect_y1 = int(width * 0.11), int(height * 0.05)
    rect_x2, rect_y2 = int(width * 0.89), int(height * 0.70)
    rect_w = rect_x2 - rect_x1
    rect_h = rect_y2 - rect_y1
    album_cover = album_cover.resize((rect_w, rect_h))
    img.paste(album_cover, (rect_x1, rect_y1))

    text = f"{artist} - {title}"
    font = get_font_size(draw, text, 1000, "arial.ttf", 65)  # max_width = 1000px
    draw.text((width // 2, int(height * 0.85)), text, fill=(255, 255, 255), font=font, anchor="mm")

    return img
