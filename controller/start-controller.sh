#!/bin/bash

gunicorn -b :8888 controller:app