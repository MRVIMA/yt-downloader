"""`python -m yt_downloader` launches the GUI; pass --cli to use the command line."""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "--cli":
    from yt_downloader.cli import main

    raise SystemExit(main(sys.argv[2:]))

from yt_downloader.gui.app import main

raise SystemExit(main())
