#!/usr/bin/env python3
"""
Minimal local MAP sender for VSP-only MAP validation.

Reads MAP text files, selects one MAP payload, and sends raw J2735 bytes to the
VSP WirelessMsgDecoder fixed UDP port.
"""

import argparse
import re
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path


WIRELESS_MSG_DECODER_PORT = 10002
MAP_MESSAGE_ID = "0012"


@dataclass
class MapSection:
    street: str | None
    intersection_id: int | None
    payload_hex: str


def clean_hex(value):
    return "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")


def is_hex_payload_line(value):
    compact = "".join(value.split())
    return bool(compact) and all(ch in "0123456789abcdefABCDEF" for ch in compact)


def parse_map_sections(input_path):
    sections = []
    current_street = None
    current_intersection_id = None
    collecting_payload = False
    payload_parts = []

    def finish_section():
        nonlocal current_street, current_intersection_id, collecting_payload, payload_parts
        if payload_parts:
            sections.append(
                MapSection(
                    street=current_street,
                    intersection_id=current_intersection_id,
                    payload_hex=clean_hex("".join(payload_parts)).lower(),
                )
            )
        collecting_payload = False
        payload_parts = []

    with input_path.open("r", encoding="utf-8") as input_file:
        for raw_line in input_file:
            line = raw_line.strip()
            if not line:
                continue

            intersection_match = re.match(r"^Intersection\s+ID\s*:\s*(\d+)\s*$", line, re.IGNORECASE)
            if intersection_match:
                if collecting_payload and payload_parts:
                    finish_section()
                current_intersection_id = int(intersection_match.group(1))
                continue

            if re.match(r"^MAP\s*:\s*$", line, re.IGNORECASE):
                collecting_payload = True
                payload_parts = []
                continue

            if collecting_payload:
                if is_hex_payload_line(line):
                    payload_parts.append(clean_hex(line))
                    continue

                finish_section()
                current_street = line
                current_intersection_id = None
                continue

            current_street = line
            current_intersection_id = None

    if collecting_payload and payload_parts:
        finish_section()

    return sections


def select_section(sections, street=None, intersection_id=None):
    matches = sections

    if street:
        expected = street.strip().casefold()
        matches = [section for section in matches if (section.street or "").strip().casefold() == expected]

    if intersection_id is not None:
        matches = [section for section in matches if section.intersection_id == intersection_id]

    if not matches:
        selectors = []
        if street:
            selectors.append(f"street={street!r}")
        if intersection_id is not None:
            selectors.append(f"intersection-id={intersection_id}")
        selector_text = ", ".join(selectors) if selectors else "first available section"
        raise ValueError(f"no MAP section matched {selector_text}")

    return matches[0]


def payload_from_section(section):
    map_index = section.payload_hex.find(MAP_MESSAGE_ID)
    if map_index < 0:
        raise ValueError("selected MAP payload does not contain J2735 MAP message ID 0012")

    payload_hex = section.payload_hex[map_index:]
    if len(payload_hex) % 2 != 0:
        raise ValueError("selected MAP payload has an odd number of hex characters")

    try:
        raw_payload = bytes.fromhex(payload_hex)
    except ValueError as exc:
        raise ValueError("selected MAP payload is not valid hex") from exc

    return payload_hex, raw_payload, map_index


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay raw J2735 MAP bytes to the VSP WirelessMsgDecoder fixed "
            f"UDP port {WIRELESS_MSG_DECODER_PORT}."
        )
    )
    parser.add_argument("--input", required=True, help="MAP text file")
    parser.add_argument("--target-ip", default="127.0.0.1", help="VSP host/container IP")
    parser.add_argument("--street", help="select MAP section by street name")
    parser.add_argument("--intersection-id", type=int, help="select MAP section by intersection ID")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between MAP sends")
    parser.add_argument("--count", type=int, help="stop after this many sends")
    parser.add_argument("--duration", type=float, help="stop after this many seconds")
    parser.add_argument("--dry-run", action="store_true", help="validate selection and print planned sends without UDP output")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)

    if args.interval <= 0:
        print("--interval must be greater than zero", file=sys.stderr)
        return 2
    if args.count is not None and args.count <= 0:
        print("--count must be greater than zero", file=sys.stderr)
        return 2
    if args.duration is not None and args.duration <= 0:
        print("--duration must be greater than zero", file=sys.stderr)
        return 2

    try:
        sections = parse_map_sections(input_path)
        if not sections:
            raise ValueError(f"no MAP sections found in {input_path}")
        section = select_section(sections, args.street, args.intersection_id)
        payload_hex, raw_payload, map_index = payload_from_section(section)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Selected MAP from {input_path}")
    print(f"Street: {section.street or 'unknown'}")
    print(f"Intersection ID: {section.intersection_id if section.intersection_id is not None else 'unknown'}")
    print(f"Payload length: {len(raw_payload)} byte(s), {len(payload_hex)} hex character(s)")
    print(f"MAP message ID {MAP_MESSAGE_ID} found at selected payload offset {map_index}")
    print(f"Target: {args.target_ip}:{WIRELESS_MSG_DECODER_PORT}")
    print(f"Interval: {args.interval:.3f} second(s)")

    if args.dry_run:
        if args.count is None and args.duration is None:
            print("Dry run: would send continuously until interrupted")
        elif args.count is not None:
            print(f"Dry run: would send {args.count} MAP message(s)")
        else:
            print(f"Dry run: would send for up to {args.duration:.3f} second(s)")
        return 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sent = 0
    started_at = time.monotonic()

    try:
        while True:
            if args.duration is not None and time.monotonic() - started_at >= args.duration:
                print(f"Done. Sent {sent} MAP message(s).")
                return 0

            sock.sendto(raw_payload, (args.target_ip, WIRELESS_MSG_DECODER_PORT))
            sent += 1
            if sent == 1 or sent % 10 == 0:
                print(f"Sent {sent} MAP message(s)")

            if args.count is not None and sent >= args.count:
                print(f"Done. Sent {sent} MAP message(s).")
                return 0

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nInterrupted. Sent {sent} MAP message(s).")
        return 0
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
