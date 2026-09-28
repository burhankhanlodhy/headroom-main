"""Backwards compatibility - CLI moved to horizon.cli package."""

from horizon.cli import main

if __name__ == "__main__":
    main()
