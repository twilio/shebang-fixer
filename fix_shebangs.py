import argparse
import contextlib
import logging
import os
import sys
import subprocess

parser = argparse.ArgumentParser()
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
            sed = 'sed -i.bak -E -e'
        else:
            sed = 'sed -i.bak -r -e'

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

