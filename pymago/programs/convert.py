from pymago.process import piped, convert
import subprocess
import sys
import os

def execute(args):
    if not args.to_format:
        print("Arg -format required to convert")
        sys.exit(1)

    for path in args.paths:
        filename, extension = os.path.splitext(path)
        new_path = '%s%s.%s' % (
            filename,
            args.suffix,
            args.to_format,
        )
        convert(path, new_path,
            resize=args.resize,
            quality=args.quality,
        )
