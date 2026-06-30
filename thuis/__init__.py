import os, sys
package_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'thuis')
if os.path.isdir(package_dir):
    __path__.append(package_dir)
try:
    from . import downloader_yt  # noqa: F401
except ImportError:
    pass