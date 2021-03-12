from __future__ import print_function
import subprocess
from datetime import datetime
from pymago.programs import convert as convert_program
from pymago.process import piped, convert, touch
import pymago

def identify(file):
    p = piped(['identify',
        '-format','%[fx:w],%[fx:h],%m,%A', file
    ])
    o, e = p.communicate()

    if p.returncode > 0:
        return None

    return ImageIdentity(o)

def pngquant(src, quality=None):
    params = ['pngquant', '--force', '--ext', '.png']

    if quality:
        params.append('-q')
        params.append(str(quality))

    params.append(src)

    p = piped(params)
    o, e = p.communicate()

def tint(filename, color, args=None):
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

    if not args or not args.dry_run:
        new_image.save(filename)

class ImageIdentity:
    def __init__(self, raw):
        data = raw.split(b',')
        self.size = int(data[0])
        self.width = int(data[0])
        self.height = int(data[1])

        if len(data) > 2:
            self.format = data[2].lower()
        else:
            self.format = None

        if len(data) > 3:
            alpha = data[3].lower()
            self.is_transparent = (
                alpha.startswith(b'blend')
                    or alpha.startswith(b'true')
            )
        else:
            self.is_transparent = False


def run():
    import os
    import sys
    import shutil
    from argparse import ArgumentParser

    parser = ArgumentParser('pymago',
        description=('You can practically convert images from '
                     'storage in your hdd or an database.'
                     ),
        epilog='I hope this is explicit enough'
    )
    parser.add_argument('subprogram', nargs=1)
    parser.add_argument('paths', nargs='*')
    parser.add_argument('-m', dest='max_size', type=int,
                        help=('If the given image(s) is bigger '
                              'than this width, will be resized, '
                              'otherwise skipped.'
                              )
                        )
    parser.add_argument('-s', dest='size', type=int,
                        help=('Downsize or upsize without exception '
                              'to the given width.')
                        )
    parser.add_argument('-f', '-format', dest='to_format',
                        help='jpg, png or gif',
                        choices=['jpg', 'png', 'gif', 'webp', 'tiff', 'bmp']
                        )
    parser.add_argument('-resize', dest='resize')
    parser.add_argument('-v', dest='is_verbose',
                        action='store_const',
                        const=True, default=False,
                        help=('Prints information about the conversion '
                              'and skips.'),
                        )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + pymago.__version__)
    parser.add_argument('--keep-mtime', action='store_const',
                        const=True, default=False, dest='keep_mtime',
                        help=('Motification time will be the same as '
                              'before the conversion.'),
                        )
    parser.add_argument('--keep-extension', action='store_const', const=True,
                        default=False, dest='keep_extension'
                        )
    parser.add_argument('-q', dest='quality', type=int,
                        help='Quality from 0 to 100.'
                        )
    parser.add_argument('-if-size', dest='if_size')
    parser.add_argument('--if-opaque', action='store_const',
                        const=True, default=False, dest='if_opaque'
                        )
    parser.add_argument('--dry-run', action='store_const', const=True,
                        default=False, dest='dry_run'
                        )
    parser.add_argument('-suffix', dest='suffix', default="")

    # Database
    parser.add_argument('-d', dest='dsn',
                        help=('Determines the database dsn for obtaining '
                              'the list of images data.')
                        )

    # General colors
    parser.add_argument('-color', dest='color',
                        default='black',
                        help=('The selected color for tint. Can be hexadecimal')
                        )

    # Various flags
    parser.add_argument('--optimize-png', action='store_const',
                        const=True, default=False,
                        dest='optimize_png',
                        help=('When FORMAT is set PNG, the final image '
                              'will also be optimized with pngquant if '
                              'available.')
                        )
    parser.add_argument('--monochrome', action='store_const',
                        const=True, default=False,
                        dest='mono',
                        help='Monochrome image.'
                        )
    parser.add_argument('--rowid', dest='db_row_id')

    args = parser.parse_args()
    subprogram = args.subprogram[0]

    if subprogram == 'resizer':

        for file in args.paths:
            p = piped(
                ['identify', '-format', '%[fx:w]', file],
            )

            o, e = p.communicate()

            if p.returncode != 0:
                continue
                
            w = int(o.split()[0])

            if args.max_size and w > args.max_size:
                try:
                    stat = os.stat(file)
                    convert(file, file, 
                            size=args.max_size,
                            quality=args.quality
                            )
                    newstat = os.stat(file)

                    if args.keep_mtime:
                        touch(file, mt=stat.st_mtime)

                    if args.is_verbose:
                        print('{0} {1} -> {2} ({3}%)'.format(
                            file, stat.st_size, newstat.st_size,
                            100 - (newstat.st_size * 100 / stat.st_size),
                        ))

                except Exception as ex:
                    print('{0} failed'.format(file), file=sys.stderr)

    elif subprogram == 'resizer-db':
        if args.dsn.startswith('psql:'):
            import psycopg2
            parts = args.dsn.split(':')
            conn = psycopg2.connect(parts[1])
            table = parts[2]
            column = parts[3]
            cursor = conn.cursor()
            params = None
            query = 'select id, "{0}" from "{1}"'

            if args.db_row_id:
                params = (args.db_row_id, )
                query += ' where id = %s'

            query = query.format(column, table)
            cursor.execute(query, params)

            total_old_size = 0
            total_new_size = 0
            
            for row in cursor:
                tempfile = '/tmp/pymago-123'
                rowid, imgdata = row

                if not imgdata:
                    print('{0} is null, ignoring'.format(imgdata))
                    continue

                old_size = len(imgdata)
                total_old_size += old_size

                with open(tempfile, 'w') as fp:
                    fp.write(str(imgdata))

                info = identify(tempfile)
                
                if args.to_format:
                    dest_filename = tempfile + '.' + args.to_format
                else:
                    dest_filename = tempfile + '.' + info.format

                imgsize = None

                if args.max_size and info.size > args.max_size:
                    imgsize = args.max_size
                elif args.size:
                    imgsize = args.size

                convert(tempfile, dest_filename,
                        quality=args.quality,
                        size=imgsize,
                        mono=args.mono,
                        )

                if args.optimize_png:
                    pngquant(dest_filename, quality=args.quality)

                with open(dest_filename, 'rb') as fp:
                    query = 'update "{0}" set "{1}" = %s where id = %s'
                    query = query.format(table, column)
                    c = conn.cursor()
                    ba = bytearray(fp.read())
                    new_size = len(ba)
                    total_new_size += new_size

                    c.execute(query, (ba, rowid))

                    if not args.dry_run:
                        conn.commit()
                    else:
                        conn.rollback()

                if args.is_verbose:
                    print('{0} --> {1} (id: {2})'\
                        .format(old_size, new_size, rowid))

            if args.is_verbose:
                print('total: {0} --> {1}'\
                    .format(total_old_size, total_new_size))

    elif subprogram == 'pngquant':
        if args.if_size:
            expected_width, expected_height = [
                int(x) for x in args.if_size.split('x')
            ]
        else:
            expected_width, expected_height = None, None

        for file in args.paths:
            info = identify(file)

            if not info:
                print('cannot idenfity {0}'.format(file))
                continue

            if args.if_size:
                if expected_width != info.width \
                or expected_height != info.height:
                    continue

            if not args.dry_run:
                pngquant(file)

            print('converted {0}'.format(file))

    elif subprogram == 'png2jpeg':
        for file in args.paths:
            info = identify(file)
            dest_file = file + '.jpg'

            if not info:
                print('cannot indentify: {0}'.format(file))
                continue

            if args.if_opaque:
                if info.is_transparent:
                    continue

            if not args.dry_run:
                convert(file, dest_file)
                if args.keep_extension:
                    shutil.move(dest_file, file)

            print('converted: {0}'.format(file))

    elif subprogram == 'convert':
        convert_program.execute(args)

    elif subprogram == 'tint':
        for file in args.paths:
            tint(file, args.color, args=args)

    else:
        print('invalid subprogram: {0}'.format(subprogram),
              file=sys.stderr
              )
        sys.exit(1)

if __name__ == '__main__':
    run()