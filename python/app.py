"""NTK.Ai.Metatrader Desktop Application Launcher.

Developed by Ali Karavi (https://alikaravi.com/)
Inspired by metatrader-ai (jblanked) and AI-Trader (HKUDS).
"""

import os
import sys

# Ensure local package path is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from metatrader_ai.app import launch

if __name__ == "__main__":
    # Launch GUI with the built-in Settings page (no hardcoded config files needed)
    launch()
