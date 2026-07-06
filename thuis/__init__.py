import os
package_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'thuis')
if os.path.isdir(package_dir):
    __path__.append(package_dir)
