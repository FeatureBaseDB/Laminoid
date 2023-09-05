#!/bin/bash

gunicorn -b 0.0.0.0:8888 sloth:app -w 2 &
