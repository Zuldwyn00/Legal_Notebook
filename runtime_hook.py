import os
import sys

# Set working directory to the bundle directory so .env file can be found
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    os.chdir(bundle_dir)
