"""`python -m batch_downloader` opens the app; with a URL it runs the command line."""

import sys


def main():
    if len(sys.argv) > 1:
        from .cli import main as cli_main
        return cli_main()
    from .app import run
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
