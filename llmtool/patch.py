"""
Utils for applying patches
"""

import subprocess

from tempfile import NamedTemporaryFile


def apply_patch(patch: str):
    subprocess.run(["patch"], input=patch, text=True, check=True)
    print("patch applied!\n\n")
