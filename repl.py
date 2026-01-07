#!/usr/bin/env python3
"""
Rigol DP832A Interactive REPL

Commands:
  status [ch]          - Show channel status (default: all)
  set <ch> <v> <a>     - Set voltage and current
  on <ch>              - Turn output on
  off <ch>             - Turn output off
  alloff               - Turn all outputs off
  v <ch> <voltage>     - Set voltage only
  i <ch> <current>     - Set current only
  measure <ch>         - Show measurements
  raw <command>        - Send raw SCPI command
  help                 - Show this help
  quit                 - Exit
"""

import sys
import readline  # enables arrow keys, history
from rigol import RigolDP832A, DEFAULT_DEVICE


def print_status(psu, channel=None):
    """Print channel status."""
    channels = [channel] if channel else [1, 2, 3]

    print(f"\n{'CH':<4} {'OUT':<5} {'V SET':<8} {'I SET':<8} {'V MEAS':<9} {'I MEAS':<9} {'POWER':<8}")
    print("-" * 60)

    for ch in channels:
        s = psu.status(ch)
        out = "ON" if s.output else "OFF"
        print(f"{ch:<4} {out:<5} {s.voltage_set:<8.3f} {s.current_set:<8.3f} "
              f"{s.voltage:<9.4f} {s.current:<9.4f} {s.power:<8.3f}")
    print()


def print_help():
    print(__doc__)


def main():
    device = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DEVICE

    print(f"Connecting to {device}...")
    try:
        psu = RigolDP832A(device)
        print(f"Connected: {psu.idn}\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    print("Type 'help' for commands, 'quit' to exit.\n")

    while True:
        try:
            line = input("rigol> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd in ('quit', 'exit', 'q'):
                print("Bye!")
                break

            elif cmd == 'help':
                print_help()

            elif cmd == 'status':
                ch = int(args[0]) if args else None
                print_status(psu, ch)

            elif cmd == 'set':
                ch, v, i = int(args[0]), float(args[1]), float(args[2])
                psu.set_voltage(ch, v)
                psu.set_current(ch, i)
                print(f"CH{ch}: {v}V, {i}A")

            elif cmd == 'on':
                ch = int(args[0])
                psu.output_on(ch)
                print(f"CH{ch} ON")

            elif cmd == 'off':
                ch = int(args[0])
                psu.output_off(ch)
                print(f"CH{ch} OFF")

            elif cmd == 'alloff':
                psu.all_off()
                print("All outputs OFF")

            elif cmd == 'v':
                ch, v = int(args[0]), float(args[1])
                psu.set_voltage(ch, v)
                print(f"CH{ch}: {v}V")

            elif cmd == 'i':
                ch, i = int(args[0]), float(args[1])
                psu.set_current(ch, i)
                print(f"CH{ch}: {i}A")

            elif cmd == 'measure':
                ch = int(args[0])
                v = psu.measure_voltage(ch)
                i = psu.measure_current(ch)
                p = psu.measure_power(ch)
                print(f"CH{ch}: {v:.4f}V  {i:.4f}A  {p:.3f}W")

            elif cmd == 'raw':
                scpi = ' '.join(args)
                if '?' in scpi:
                    result = psu.query(scpi)
                    print(f"< {result}")
                else:
                    psu.command(scpi)
                    print("OK")

            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")

        except IndexError:
            print("Missing arguments. Type 'help' for usage.")
        except ValueError as e:
            print(f"Invalid value: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()
