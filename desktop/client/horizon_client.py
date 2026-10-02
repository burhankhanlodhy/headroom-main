"""Frozen entry point for the Horizon client shipped inside the desktop app.

The desktop launcher runs this executable for the commands it needs on the
user's machine: ``forward start`` (loopback relay to the hosted proxy),
``vault`` (device key in Windows Credential Manager) and ``wrap`` /
``unwrap`` (point a locally installed tool at the relay). No Python install
is required on the user's machine.
"""

import multiprocessing

from horizon.cli.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main(prog_name="horizon")
