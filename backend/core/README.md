# Getting Started
1. Build docker image ```docker build . -t coralcompanion/backend-core:0.1```
1. If not present already, create the docker network ```docker network create coral-companion-network```
1. Run docker container ```docker run -p 8080:8000 --network coral-companion-network --name backend-core -d coralcompanion/backend-core:0.1```
