#!/bin/bash
set -e
cd /home/raphael/Desktop/SteamSalesMonitor
git pull --ff-only
./venv/bin/python main.py
