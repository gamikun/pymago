from __future__ import print_function
import subprocess


def identify(file):
    p = subprocess.Popen(
        ['identify', '-format', '%[fx:w],%m', file],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    o, e = p.communicate()

    if p.returncode > 0:
        return None

    return ImageIdentity(o)

def convert(src, dest, quality=None, size=None, mono=False):
    params = ['convert']

    if quality:
        params.append('-quality')
        params.append(str(quality))

    if size:
        params.append('-resize')
        params.append(str(size))

    if mono:
        params.append('-monochrome')

    params.append(src)
    params.append(dest)

    p = subprocess.Popen(params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    o, e = p.communicate()
    print(o, e)

def pngquant(src, quality=None):
    params = ['pngquant', '--force', '--ext', '.png']

    if quality:
        params.append('-q')
        params.append(str(quality))

    params.append(src)

    p = subprocess.Popen(params,
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE
    )

    o, e = p.communicate()

class ImageIdentity:
    def __init__(self, raw):
        data = raw.split(',')
        self.size = int(data[0])
        self.format = data[1].lower()


if __name__ == '__main__':
    import os
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('subprogram', nargs=1)
    parser.add_argument('paths', nargs='*')
    parser.add_argument('-m', dest='max_size', type=int)
    parser.add_argument('-s', dest='size', type=int)
    parser.add_argument('-f', dest='to_format')
    parser.add_argument('--keep-mtime', action='store_const',
                        const=True, default=False, dest='keep_mtime',
                        )
    parser.add_argument('-q', dest='quality', type=int)

    # Database
    parser.add_argument('-d', dest='dsn')

    # Various flags
    parser.add_argument('--optimize-png', action='store_const',
                        const=True, default=False,
                        dest='optimize_png'
                        )
    parser.add_argument('--monochrome', action='store_const',
                        const=True, default=False,
                        dest='mono'
                        )

    args = parser.parse_args()
    subprogram = args.subprogram[0]

    if subprogram == 'resizer':

        for file in args.paths:
            p = subprocess.Popen(
                ['identify', '-format', '%[fx:w]', file],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )

            o, e = p.communicate()

            if p.returncode != 0:
                continue
                
            w = int(o.split()[0])

            if args.max_size and w > args.max_size:
                try:
                    stat = os.stat(file)
                    subprocess.check_call([
                        'convert', '-resize', str(args.max_size),
                        file, file
                    ])
                    newstat = os.stat(file)
                    print('{0} {1} -> {2} ({3}%)'.format(
                        file, stat.st_size, newstat.st_size,
                        100 - (newstat.st_size * 100 / stat.st_size),
                    ))

                except Exception as ex:
                    raise
                    #print(ex )
                    print('{0} failed'.format(file), file=sys.stderr)

    elif subprogram == 'resizer-db':
        if args.dsn.startswith('psql:'):
            import psycopg2
            parts = args.dsn.split(':')
            conn = psycopg2.connect(parts[1])
            table = parts[2]
            column = parts[3]
            cursor = conn.cursor()
            query = 'select id, "{0}" from "{1}"'
            query = query.format(column, table)
            cursor.execute(query)

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
                    conn.commit()

                print('{0} --> {1} (id: {2})'.format(old_size, new_size, rowid))
                #break


            print('total: {0} --> {1}'\
                .format(total_old_size, total_new_size))

    else:
        print('invalid subprogram: {0}'.format(subprogram))
        sys.exit(1)
