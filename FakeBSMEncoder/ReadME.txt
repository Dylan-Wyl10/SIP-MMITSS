Folder "FakeBSMEncoder" should be placed in edge on vehilce side. It has the folloiwng features:
1. bsm_encoder.py
    Encoder bsm from VISSIM driving_model.dll to a SAE J2735 BSM payload and restore the payloads as a file "fake_bsm.txt". Configuration includes  VISSIM ip and restore path. 
    This python script is used for read the pre-recorded BSM from fake_bsm.txt and distribute to MMITSS vsp docker and OBU. 
