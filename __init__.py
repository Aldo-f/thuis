import os
print(f"[DEBUG] Loading __init__.py from {__file__}")
# Include inner 'thuis' package and 'src/thuis' in this package's search path
package_dir = os.path.join(os.path.dirname(__file__), 'thuis')
if os.path.isdir(package_dir):
    __path__.append(package_dir)
# src_dir = os.path.join(os.path.dirname(__file__), 'src', 'thuis')
# if os.path.isdir(src_dir):
#     __path__.append(src_dir)