# MMITSS VSP MAP Validation

This package helps collaborators test whether a candidate J2735 MAP activates inside MMITSS VSP/LocAware/PRG logic using the VSP Docker container and local replay tools.

See [MMITSS VSP MAP Validation Tool Guide](<MMITSS VSP MAP Validation Tool Guide.md>) for full setup and usage.

Quick start:

1. Start the VSP Docker container with `nojournal/` mounted.
2. Run `python3 replay_tools/fake_map.py --input examples/maps/M1_MAP_info.txt --street "Warren Avenue" --target-ip <vsp_ip>`.
3. Run `python3 replay_tools/fake_bsm_local.py --input examples/bsm_inputs/Warren_N2S.txt --target-ip <vsp_ip> --loop`.
4. Parse the newest PRG log with `python3 replay_tools/parse_prg_status.py --input nojournal/bin/log/<vehicle_prgLog_xxx.log> --tail 5000`.
5. Treat only active MAP plus `OnMAP=True` with reasonable `laneID`/`signalGroup` as a pass.

