"""
Ensure the backend package root is importable.

Lets `pytest` run from the repository root, from `Project/`,
or from `Project/backend/` with identical results.
"""

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
