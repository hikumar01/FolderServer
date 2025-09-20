#!/bin/bash
python3 server.py $(ipconfig getifaddr en0)
echo "test"
