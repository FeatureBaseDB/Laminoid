#!/bin/bash

conda activate sloth
gunicorn -b 0.0.0.0:8888 sloth:app -w 4 &
