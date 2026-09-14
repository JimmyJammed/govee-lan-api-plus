"""Optional capture runner: python -m govee_lan_api_plus.capture PROCESS SCRIPT OUTPUT.

SCRIPT must be a Frida-version-compatible compiled hook supplied by the user.
Captured messages may contain account data; keep OUTPUT private.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('process')
    parser.add_argument('script')
    parser.add_argument('output')
    args = parser.parse_args()
    try:
        import frida
    except ImportError:
        parser.exit(1, "Install the capture extra: pip install 'govee-lan-api-plus[capture]'\n")
    device = frida.get_usb_device(timeout=5)
    session = device.attach(int(args.process) if args.process.isdecimal() else args.process)
    try:
        with open(args.output, 'x') as output:
            def received(message, data):
                output.write(json.dumps(message) + '\n')
                output.flush()
            script = session.create_script(Path(args.script).read_text())
            script.on('message', received)
            script.load()
            print('Attached. Press Enter to detach.', file=sys.stderr)
            input()
    finally:
        session.detach()


if __name__ == '__main__':
    main()
