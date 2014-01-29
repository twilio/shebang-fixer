from __future__ import division
import argparse
import contextlib
import logging
import os
import string
import sys
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--no-backup', action='store_true', help="Don't backup altered files")
parser.add_argument('current_venv_path', help='The path to virtual environment')
parser.add_argument('target_venv_path', help='The location of the new bin')
args = parser.parse_args()

logging.basicConfig()
logger = logging.getLogger("shebang-fixer")
#logger.setLevel(logging.DEBUG)
VENV_DIR = "venv"

if os.path.isabs(args.current_venv_path):
    current_venv_path = args.current_venv_path
    venv_bin_path = os.path.join(current_venv_path, "bin")
else:
    current_venv_path = os.path.join(os.getcwd(), args.current_venv_path)
    venv_bin_path = os.path.join(current_venv_path, "bin")

if os.path.isabs(args.target_venv_path):
    target_venv_path = args.target_venv_path
    target_venv_bin_path = os.path.join(target_venv_path, "bin")
else:
    target_venv_path = os.path.join(os.getcwd(), args.target_venv_path)
    target_venv_bin_path = os.path.join(target_venv_path, "bin")

if args.no_backup:
    backup_extension = ''
else:
    backup_extension = '.bak'

def istext(filename):
    s = open(filename).read(512)
    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    if not s:
        # Empty files are considered text
        return True
    if "\0" in s:
        # Files with null bytes are likely binary
        return False
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_null_trans, text_characters)
    # If more than 30% non-text characters, then
    # this is considered a binary file
    if len(t)/len(s) > 0.30:
        return False
    return True

@contextlib.contextmanager
def cd(path):
    prevdir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prevdir)

def run(cmd):
    logger.debug("Executing command: '{}'".format(cmd))
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        logger.debug(output)
    except subprocess.CalledProcessError as e:
        if 'illegal byte sequence' in e.output:
            return
        logger.debug(e.output)
        raise

    return output

with cd(venv_bin_path):
    for script in os.listdir(venv_bin_path):
        if sys.platform == "darwin":
            # assume BSD sed
            sed = 'sed -i%s -E -e' % backup_extension
        else:
            sed = 'sed -i%s -r -e' % backup_extension

        if not istext(script):
            logger.debug("skipping {} as it is a binary".format(script))
            continue

        old_path = ('#!' + os.path.join(current_venv_path, 'bin/(.+)')).replace("/", r"\/")
        new_path = ('#!' + os.path.join(target_venv_bin_path, r'\1')).replace("/", r"\/")

        run("{sed} 's/{old_path}/{new_path}/g' {script}".format(
            sed=sed, old_path=old_path, new_path=new_path, script=script,
        ))

        # replace for activate, activate.csh, activate.fish
        old_path = current_venv_path.replace("/", r"\/")
        new_path = target_venv_path.replace("/", r"\/")
        run("{sed} 's/{old_path}/{new_path}/g' {script}".format(
            old_path=old_path, sed=sed, new_path=new_path, script=script
        ))

