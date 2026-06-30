import os, sys
# Make this package delegate to the src/thuis package and expose top-level modules
package_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'thuis')
if os.path.isdir(package_dir):
    __path__.append(package_dir)
# Explicitly import downloader_yt to ensure it's available as thuis.downloader_yt
from . import downloader_yt  # noqa: F401