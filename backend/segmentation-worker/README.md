# Overview
This module is used to be deployed onto machines with specific attributes (e.g. machines with GPUs or many CPUs) so that segmentation can be done fast without having to use such a strong machine for all functionality of Coral Companion (such as metrics calculation, db access, some image calculations).

# Getting Started
1. Build docker image ```docker build . -t coralcompanion/segmentation-worker:0.1```
1. If not present already, create the docker network ```docker network create coral-companion-network```
1. Run docker container ```docker run -p 8081:8000 --network coral-companion-network --name segmentation-worker -d coralcompanion/segmentation-worker:0.1```


# Acknowledgements

## CoralSCOP
This project uses CoralSCOP, developed by Wong et al., for coral segmentation. It has proven to be extremely helpful for this project. CoralSCOP has been cloned and its code is accessed under backend/third_party.

CoralSCOP:
https://github.com/zhengziqiang/CoralSCOP

Paper:
CoralSCOP-LAT: Labeling and Analyzing Tool for Coral Reef Images with Dense Mask

Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0):
https://creativecommons.org/licenses/by-nc-sa/4.0/

The Coral Companion project integrates CoralSCOP as a preprocessing step for coral segmentation before colony matching. The only modifications have been made to integrate the model into this application (eg. adjusting imports and adding log statements for debugging purposes).
