This folder includes the necessary configerations for implementing MMITSS in MCity. 

1. MCity_map:
  - parent and child map of MCity based on the USDOT tools. (https://webapp.connectedvcs.com/isd/). The parent map is used for changing the reference points and speed limit, while the child map is for setting signal phase group. In our hardware in the loop simulation, I have tried to fit the signal phase group based on an old phase table provided by Dr.Feng. But I am not sure whether it has been changed during these two year. If there is anything need me to modify on the MAP message, please feel free to contact Yilin.  
  - Map payload for MMITSS configerations generated from USDOT tools abover

2.  MMITSS_config:
  - MCity_MRP_Sample
  - MCity_VSP_Sample
  
  Note:These two folder is the configuration folder for building MMITSS VSP/MRP. The path start with "../nojournal/.." For example, when excuating the scripts named "launch-container.sh", the absolute path for configuration file should be "$ROOT/SIP_MCity_config/MMITSS_config/MCity_MRP_Sample/nojournal" 

3. MMITSS HIL Simulation Setup Guidance 
   Note: this is the detailed documentation for setting up MMITSS with Hardware in the loop framework. 