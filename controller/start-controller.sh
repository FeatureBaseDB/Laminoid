#!/bin/bash

gunicorn -b :7878 controller:app