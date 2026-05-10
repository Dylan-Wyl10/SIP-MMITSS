# MMITSS VSP MAP Validation Tool

## 1. Purpose

This tool simulates the MMITSS end-to-end MAP validation process using only the VSP Docker container and local replay scripts. It enables us to test whether a candidate MAP works in MMITSS without setting up OBU, RSU, MRP, signal controller, or radio hardware.

The result is determined from the VSP PRG log. If the MAP becomes active and SRM messages are generated, then the MAP works for the VSP-side end-to-end MAP validation logic. 

## 2. Tool location and package structure

The tool package is available in the SIP-MMITSS GitHub repository:

```text
https://github.com/Dylan-Wyl10/SIP-MMITSS/tree/main
```

Repository path:

```text
SIP-MMITSS/MRP1211_2025Sep/MMITSS_VSP_Map_Validation
```

After downloading or cloning the repository, enter the tool folder:

```bash
cd SIP-MMITSS/MRP1211_2025Sep/MMITSS_VSP_Map_Validation
```

Package structure:

- `install_script/`: VSP container launch scripts.
- `nojournal/`: VSP configuration and generated logs.
- `replay_tools/`: MAP replay, BSM replay, and PRG log parser scripts.
- `examples/maps/`: MAP text files for testing.
- `examples/bsm_inputs/`: BSM files for different intersections and directions.
- `examples/expected_results/`: example parser outputs for reference.

## 3. System requirements

- Ubuntu-based x86 device.
- Ubuntu 20.04 LTS recommended.
- Docker installed.
- Docker image: `cartlabpurdue/mmitss-vsp-x86:AA1.2`

```bash
docker pull cartlabpurdue/mmitss-vsp-x86:AA1.2
```

## 4. Configuration

Update `HostIp` according to your VSP device IP in:

```text
nojournal/bin/mmitss-phase3-master-config.json
```

Example:

```json
"HostIp": "192.168.0.101"
```

VSP PRG logs are generated under:

```text
nojournal/bin/log/
```

Example log name:

```text
vehicle_prgLog_05102026_170422.log
```

## 5. Start the VSP Docker container

Create the log directory:

```bash
mkdir -p <absolute-path-to-mmitss-vsp>/nojournal/bin/log
```

Run the launch script:

```bash
cd install_script
chmod +x launch-container.sh
sudo ./launch-container.sh
```

The script prompts for:

```text
Full absolute path of MMITSS configuration directory:
<absolute-path-to-mmitss-vsp>/nojournal

Name of container image on DockerHub:
cartlabpurdue/mmitss-vsp-x86:AA1.2

Name of container:
vsp_container

Timezone:
America/New_York
```

Basic Docker commands:

```bash
docker ps
docker exec -it <container_name> /bin/bash
docker stop <container_name>
docker start <container_name>
docker restart <container_name>
```

## 6. Prepare MAP and BSM inputs

MAP files should follow the same format as `M1_MAP_info.txt`:

```text
Warren Avenue
Intersection ID: 14467
MAP:
0012...
```

To test a new MAP, add a new section or replace the MAP payload in a MAP text file. Keep the street name line consistent with what will be passed to `--street`. Update the `Intersection ID:` line to match the MAP being tested. The MAP payload should be the encoded MAP string.

Select a MAP by intersection ID:

```bash
python3 replay_tools/fake_map.py \
  --input examples/maps/M1_MAP_info.txt \
  --intersection-id 14467 \
  --target-ip 192.168.0.101
```

`examples/bsm_inputs/` should include BSM files for all seven intersections and available directions. Examples include Antoinette, Baltimore, Burroughs, Kirby, Palmer, Putnam, and Warren, with direction variants such as `N2S`/`S2N`.

Choose the BSM file that matches the tested intersection and travel direction. For Warren Avenue north-to-south, use `Warren_N2S.txt`.

## 7. Run one MAP validation test

For each test, restart the VSP Docker container first. This gives a fresh PRG log file and avoids mixing results from previous tests. After restarting, use the newest PRG log file under `nojournal/bin/log/` for the parser command.

Use four terminals.

### Terminal 1: restart VSP

```bash
docker restart vsp_container
```

### Terminal 2: replay MAP every 2 seconds

```bash
python3 replay_tools/fake_map.py \
  --input examples/maps/M1_MAP_info.txt \
  --street "Warren Avenue" \
  --target-ip 192.168.0.101
```

### Terminal 3: replay matching BSM at 10 Hz

```bash
python3 replay_tools/fake_bsm_local.py \
  --input examples/bsm_inputs/Warren_N2S.txt \
  --target-ip 192.168.0.101 \
  --loop
```

### Terminal 4: parse the newest PRG log

```bash
python3 replay_tools/parse_prg_status.py \
  --input nojournal/bin/log/<newest_vehicle_prgLog_xxx.log> \
  --tail 5000 \
  --output-json test_summary.json
```

## 8. Interpret results

- `PASS_ACTIVE_MAP`: active MAP observed and `OnMAP=True` observed.
- `MAP_AVAILABLE_BUT_INACTIVE`: MAP was received/listed, but never became active and `OnMAP` stayed false.
- `NO_MAP_OBSERVED`: PRG status found, but no MAP listed.
- `INSUFFICIENT_LOG_DATA`: no PRG status JSON found.

A passing result should include active MAP plus `OnMAP=True`, with reasonable nonzero `laneID` and `signalGroup` for the expected trajectory.

