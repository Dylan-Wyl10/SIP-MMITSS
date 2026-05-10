#!/usr/bin/env python3
"""
Summarize VSP PriorityRequestGeneratorStatus log evidence for MAP activation.
"""

import argparse
import json
import sys
from pathlib import Path


SRM_MARKERS = ("SRM String is:", "SRM is sent since")


def iter_lines(input_path, tail=None):
    with input_path.open("r", encoding="utf-8", errors="replace") as input_file:
        if tail is None:
            yield from input_file
        else:
            lines = input_file.readlines()
            yield from lines[-tail:]


def extract_json_objects(line):
    objects = []
    search_index = 0
    while True:
        start = line.find("{", search_index)
        if start < 0:
            break

        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(line)):
            char = line[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = line[start : index + 1]
                    try:
                        objects.append(json.loads(candidate))
                    except json.JSONDecodeError:
                        pass
                    search_index = index + 1
                    break
        else:
            break

    return objects


def normalize_bool_string(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return None
    return str(value)


def summarize(input_path, tail=None):
    status_count = 0
    map_observed = False
    active_observed = False
    onmap_observed = False
    request_sent_observed = False
    latest_lane_id = None
    latest_signal_group = None
    latest_maps = []
    srm_evidence = False

    for line in iter_lines(input_path, tail):
        if any(marker in line for marker in SRM_MARKERS):
            srm_evidence = True

        if "PriorityRequestGeneratorStatus" not in line:
            continue

        for json_object in extract_json_objects(line):
            status = json_object.get("PriorityRequestGeneratorStatus")
            if not isinstance(status, dict):
                continue

            status_count += 1
            host_vehicle = status.get("hostVehicle") or {}
            priority_status = host_vehicle.get("priorityStatus") or {}
            infrastructure = status.get("infrastructure") or {}

            onmap = normalize_bool_string(priority_status.get("OnMAP"))
            request_sent = normalize_bool_string(priority_status.get("requestSent"))
            if onmap == "True":
                onmap_observed = True
            if request_sent == "True":
                request_sent_observed = True

            if "laneID" in host_vehicle:
                latest_lane_id = host_vehicle.get("laneID")
            if "signalGroup" in host_vehicle:
                latest_signal_group = host_vehicle.get("signalGroup")

            available_maps = infrastructure.get("availableMaps")
            if isinstance(available_maps, list):
                latest_maps = available_maps
                if available_maps:
                    map_observed = True
                for map_entry in available_maps:
                    if isinstance(map_entry, dict) and normalize_bool_string(map_entry.get("active")) == "True":
                        active_observed = True
            elif available_maps:
                map_observed = True

    if status_count == 0:
        result = "INSUFFICIENT_LOG_DATA"
    elif active_observed and onmap_observed:
        result = "PASS_ACTIVE_MAP"
    elif active_observed:
        result = "PARTIAL_ACTIVE_ONLY"
    elif onmap_observed:
        result = "PARTIAL_ONMAP_ONLY"
    elif map_observed:
        result = "MAP_AVAILABLE_BUT_INACTIVE"
    else:
        result = "NO_MAP_OBSERVED"

    return {
        "result": result,
        "status_count": status_count,
        "map_observed": map_observed,
        "active_map_observed": active_observed,
        "onmap_true_observed": onmap_observed,
        "latest_lane_id": latest_lane_id,
        "latest_signal_group": latest_signal_group,
        "request_sent_true_observed": request_sent_observed,
        "srm_evidence_found": srm_evidence,
        "latest_available_maps": latest_maps,
    }


def print_summary(summary):
    print(f"Result: {summary['result']}")
    print(f"PRG status records: {summary['status_count']}")
    print(f"Any MAP observed: {summary['map_observed']}")
    print(f"Any availableMaps active=True: {summary['active_map_observed']}")
    print(f"Any OnMAP=True: {summary['onmap_true_observed']}")
    print(f"Latest laneID: {summary['latest_lane_id']}")
    print(f"Latest signalGroup: {summary['latest_signal_group']}")
    print(f"Any requestSent=True: {summary['request_sent_true_observed']}")
    print(f"SRM evidence found: {summary['srm_evidence_found']}")

    latest_maps = summary["latest_available_maps"]
    if latest_maps:
        print("Latest availableMaps:")
        for map_entry in latest_maps:
            if not isinstance(map_entry, dict):
                continue
            print(
                "  "
                f"{map_entry.get('DescriptiveName', 'unknown')} "
                f"IntersectionID={map_entry.get('IntersectionID', 'unknown')} "
                f"active={map_entry.get('active', 'unknown')} "
                f"age={map_entry.get('age', 'unknown')}"
            )

    if summary["result"].startswith("PARTIAL_"):
        print("Note: partial result is inconclusive; clean pass requires active=True and OnMAP=True.")


def parse_args():
    parser = argparse.ArgumentParser(description="Parse PRG status logs for MAP activation evidence")
    parser.add_argument("--input", required=True, help="VSP/PRG log or supervisor stdout capture")
    parser.add_argument("--output-json", help="optional path for JSON summary output")
    parser.add_argument("--tail", type=int, help="parse only the last N lines")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)

    if args.tail is not None and args.tail <= 0:
        print("--tail must be greater than zero", file=sys.stderr)
        return 2

    try:
        summary = summarize(input_path, args.tail)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)

    if args.output_json:
        output_path = Path(args.output_json)
        try:
            output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"error writing {output_path}: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote JSON summary to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

