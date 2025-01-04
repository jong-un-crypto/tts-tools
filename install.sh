#!/bin/bash
conda install -c conda-forge gcc -y
conda install -c conda-forge gxx -y
conda install ffmpeg cmake -y
conda install pytorch==2.5.1 torchvision==0.16.1 torchaudio==2.5.1 pytorch-cuda=12.4 -c pytorch -c nvidia
pip install -r requirements.txt
