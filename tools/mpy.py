"""Run a project script with the Mechy engine's Python (build123d, mechy.design_tools), whatever `python` is on PATH.
usage: python tools/mpy.py <script.py | -m module> [args...]
"""
import subprocess
import sys
from pathlib import Path

VENV_PY = Path("/Users/fabianarevalo/Documents/Mechy/engine/.venv/bin/python")
sys.exit(subprocess.run([str(VENV_PY), *sys.argv[1:]]).returncode)
