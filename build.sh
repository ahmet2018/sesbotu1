#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# FFmpeg genellikle Render'ın standart ortamında bulunur, 
# ancak bulunmazsa bu script üzerinden ek kurulumlar yapılabilir.
