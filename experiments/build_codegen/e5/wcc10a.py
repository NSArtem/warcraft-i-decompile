"""Compile one E5 source with Watcom 10.0a behind the short compiler mirror.

    python3 -m experiments.build_codegen.e5.wcc10a SRC OUT [CFLAGS]

`build_e5.compile_10a` runs this as a separate process with `WC1_ROOT` set to
the mirror, so wc1.oldcc's own `-i=` arguments (the repository's src/include
and the 10.0a h/) are exactly as short as the caller's source and output
paths.  Watcom 10.0a's Win32 wcc386 crashes with an access violation on long
command-line paths (rev-e5-01), so a checkout at any depth must not hand it
its own absolute paths.  Production modules are imported, never patched.
"""
import sys

from wc1 import match, oldcc


def main(argv):
    if len(argv) < 2:
        print('usage: python3 -m experiments.build_codegen.e5.wcc10a SRC OUT [CFLAGS]',
              file=sys.stderr)
        return 2
    src, out = argv[0], argv[1]
    cflags = argv[2] if len(argv) > 2 and argv[2] else match.file_cflags(src)
    try:
        oldcc.compile_c(src, cflags, out, quiet=True)
    except oldcc.OldCCTimeout as exc:
        print(f'timeout: {exc}', file=sys.stderr)
        return 78
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:        # OldCCError: toolchain or Wine missing
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
