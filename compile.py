from nestpython.files import *
import subprocess

nbuild('app-npy', 'app', erase_dir=False, replace_previous=True, transfer_other_files=True)
subprocess.call(f'python "app/main.py"')