def tint(
    filename: str,
    color: str,
    dry_run: bool = False,

):
    """ Given a PNG file, replaces all the non-transparent pixels
    with the given color. """
    try:
        from PIL import Image, ImageColor
    except ImportError:
        print('Pillow not installed.\nInstall it with pip install pillow')
        return

    image = Image.open(filename)
    width, height = image.size
    pixel_count = width * height
    data = bytearray(image.tobytes())
    r, g, b = ImageColor.getrgb(color)

    for index in range(pixel_count):
        if data[index * 4 + 3] > 0:
            data[index * 4] = r
            data[index * 4 + 1] = g
            data[index * 4 + 2] = b

    new_image = Image.frombytes(image.mode, image.size, bytes(data))

    if not dry_run:
        new_image.save(filename)        

def execute(args):
    for file in args.paths:
        tint(file, args.color, dry_run=args.dry_run)