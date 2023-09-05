#!/bin/bash

gunicorn -b 0.0.0.0:8989 sloth:app -w 2 &
