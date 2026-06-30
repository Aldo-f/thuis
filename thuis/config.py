import logging

# Base directory of the project (two levels up from this file: thuis/thuis/config.py -> thuis/thuis -> thuis -> project root)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logger for the thuis package
log = logging.getLogger('thuis')
# Add a null handler to avoid "No handlers found" warnings if logging not configured elsewhere
log.addHandler(logging.NullHandler())