# syntax=docker/dockerfile:1

FROM ubuntu:22.04
WORKDIR /app
COPY . .

# Install cv2 dependencies that are normally present on the local machine, but might be missing 
# in a Docker container
# RUN apt install ffmpeg libsm6 libxext6 -y

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
RUN apt-get update && apt-get install -y \
    build-essential \
    python3.10 \
    vim \
    git \
    ffmpeg \ 
    libsm6 \
    libxext6 \
    net-tools

RUN /bin/bash create_venv.sh


CMD ["/bin/bash", "node_demo.sh"]

# Build the image using
#   sudo docker build -t zdg -f Dockerfile .

# Run the image using
#   sudo docker run -it zdg
#   sudo docker run -it zdg bash

# Remove image using
#   sudo docker rmi -f 42af9b40137d

# Remove all stopped containers
#   sudo docker rm $(sudo docker ps --filter status=exited -q)

# Remove dnagling images (those called <none>)
#   sudo docker rmi -f $(sudo docker images -f "dangling=true" -q)

# Stop and remove all containers
#   sudo docker ps -aq | xargs sudo docker stop | xargs sudo docker rm

# Export this image to file
#   sudo docker save zdg > docker_image.tar 

# Load this image to docker
#   sudo docker load --input docker_image.tar