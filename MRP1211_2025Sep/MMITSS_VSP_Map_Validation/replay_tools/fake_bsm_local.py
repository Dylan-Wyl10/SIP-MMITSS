#!/usr/bin/env python3
"""
Minimal local FakeBSM sender for VSP-only MAP validation.

Reads hex-encoded J2735 BSM payloads and sends the unchanged raw bytes to the
VSP HostBsmDecoder fixed UDP port.
"""

import argparse
import socket
import sys
import time
from pathlib import Path


HOST_BSM_DECODER_PORT = 10005
BSM_INTERVAL_SECONDS = 0.1


def load_hex_lines(input_path):
    payloads = []
    with input_path.open("r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            hex_payload = "".join(stripped.split())
            try:
                raw_payload = bytes.fromhex(hex_payload)
            except ValueError as exc:
                raise ValueError(
                    f"{input_path}:{line_number}: invalid hex payload"
                ) from exc
            payloads.append((line_number, hex_payload, raw_payload))

    if not payloads:
        raise ValueError(f"no BSM payloads found in {input_path}")

    return payloads


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay raw J2735 BSM bytes to the VSP HostBsmDecoder fixed "
            f"UDP port {HOST_BSM_DECODER_PORT}."
        )
    )
    parser.add_argument("--input", required=True, help="BSM text file with one hex payload per line")
    parser.add_argument("--target-ip", default="127.0.0.1", help="VSP host/container IP")
    parser.add_argument("--loop", action="store_true", help="loop over the input file until interrupted")
    parser.add_argument("--max-messages", type=int, help="stop after sending this many BSM messages")
    parser.add_argument("--dry-run", action="store_true", help="validate input and print planned sends without UDP output")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)

    if args.max_messages is not None and args.max_messages <= 0:
        print("--max-messages must be greater than zero", file=sys.stderr)
        return 2

    try:
        payloads = load_hex_lines(input_path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Loaded {len(payloads)} BSM payload(s) from {input_path}")
    print(f"Target: {args.target_ip}:{HOST_BSM_DECODER_PORT}")
    print(f"Timing: one BSM every {BSM_INTERVAL_SECONDS:.1f} seconds (10 Hz)")

    if args.dry_run:
        planned = len(payloads) if args.max_messages is None else min(args.max_messages, len(payloads))
        if args.loop and args.max_messages is not None:
            planned = args.max_messages
        print(f"Dry run: would send {planned} message(s)")
        for index, (line_number, hex_payload, raw_payload) in enumerate(payloads[: min(planned, len(payloads))], start=1):
            print(
                f"  #{index}: source line {line_number}, "
                f"{len(raw_payload)} byte(s), startswith={hex_payload[:8]}"
            )
        if args.loop and args.max_messages is None:
            print("Dry run: --loop without --max-messages would run until interrupted")
        return 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = 0

    try:
        while True:
            for _, _, raw_payload in payloads:
                sock.sendto(raw_payload, (args.target_ip, HOST_BSM_DECODER_PORT))
                sent += 1
                if sent == 1 or sent % 50 == 0:
                    print(f"Sent {sent} BSM message(s)")
                if args.max_messages is not None and sent >= args.max_messages:
                    print(f"Done. Sent {sent} BSM message(s).")
                    return 0
                time.sleep(BSM_INTERVAL_SECONDS)

            if not args.loop:
                print(f"Done. Sent {sent} BSM message(s).")
                return 0
    except KeyboardInterrupt:
        print(f"\nInterrupted. Sent {sent} BSM message(s).")
        return 0
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())

