"""NTK.Ai.Metatrader - AI-Powered Trading Assistant.

Developed by Ali Karavi (https://alikaravi.com/)
Inspired by metatrader-ai (jblanked) and AI-Trader (HKUDS).
"""

import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(root_dir, "python")
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

from metatrader_ai.app import launch

if __name__ == "__main__":
    # Launch GUI with full in-app Settings configuration
    launch()
