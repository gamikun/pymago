import subprocess
from datetime import datetime

def piped(params):
    return subprocess.Popen(
        params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def convert(src, dest,
    quality=None,
    size=None,
    mono=False,
    resize=None,
    desaturate=False
):
    params = ['convert']

    if quality:
        params.append('-quality')
        params.append(str(quality))

    if resize:
        params.append('-resize')
        params.append(str(resize))

    if size:
        params.append('-resize')
        params.append(str(size))

    if mono:
        params.append('-monochrome')

    if desaturate:
        params.append('-channel')
        params.append('RGB')
        params.append('-colorspace')
        params.append('gray')
        params.append('+channel')

    params.append(src)
    params.append(dest)

    p = piped(params)
    o, e = p.communicate()

def touch(file, mt=None):
    params = ['touch']

    if mt:
        params.append('-mt')

        if isinstance(mt, float) or isinstance(mt, int):
            mt = datetime.fromtimestamp(mt)
            raw_mt = mt.strftime('%Y%m%d%H%M%S')
        else:
            raise ValueError('invalid -mt')

        params.append(str(raw_mt))

    params.append(file)

    p = piped(params)
    p.communicate()

    return p.returncode == 0

def pngquant(src, quality=None):
    params = ['pngquant', '--force', '--ext', '.png']

    if quality:
        params.append('-q')
        params.append(str(quality))

    params.append(src)

    p = piped(params)
    o, e = p.communicate()