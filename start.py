#!/usr/bin/env python3
"""Quick start script for JobPortal System"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("  JobPortal System — Starting Up")
print("=" * 50)

try:
    from flask import Flask
except ImportError:
    print("Installing Flask...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])

subprocess.run([sys.executable, 'app.py'])
