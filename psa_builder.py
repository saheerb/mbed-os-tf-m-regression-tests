#!/usr/bin/env python3
"""
Copyright (c) 2020 ARM Limited. All rights reserved.

SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import subprocess
from os.path import join, dirname, abspath, isdir
import logging
import requests
from zipfile import ZipFile

try:
    import yaml
except ImportError as e:
    print(str(e) + " To install it, type:")
    print("python3 -m pip install PyYAML")
    exit(1)


upstream_tfm = "https://git.trustedfirmware.org/TF-M/trusted-firmware-m.git"
mbed_tfm = "https://github.com/ARMmbed/trusted-firmware-m.git"

dependencies = {
    # If the remote repo is changed, please delete TARGET_IGNORE folder.
    # Quick switch between remotes is not supported.
    "tf-m": {
        "trusted-firmware-m": [mbed_tfm, "mbed-tfm-1.1"],
        "mbed-crypto": [
            "https://github.com/ARMmbed/mbed-crypto.git",
            "mbedcrypto-3.0.1",
        ],
        "mcuboot": ["https://github.com/JuulLabs-OSS/mcuboot.git", "v1.6.0"],
        "tf-m-tests": [
            "https://github.com/ARMmbed/tf-m-tests.git",
            "mbed-tfm-1.1",
        ],
    },
    "psa-api-compliance": {
        "psa-arch-tests": [
            "https://github.com/ARM-software/psa-arch-tests.git",
            "master",
        ],
    },
}

TC_DICT = {"ARMCLANG": "ARMC6", "GNUARM": "GCC_ARM"}

SUPPORTED_TFM_PSA_CONFIGS = ["ConfigPsaApiTestIPC.cmake"]
SUPPORTED_TFM_CONFIGS = [
    "ConfigCoreIPC.cmake",  # Default config
    "ConfigRegressionIPC.cmake",
] + SUPPORTED_TFM_PSA_CONFIGS

PSA_SUITE_CHOICES = [
    "CRYPTO",
    "INITIAL_ATTESTATION",
    "PROTECTED_STORAGE",
    "INTERNAL_TRUSTED_STORAGE",
    "STORAGE",
    "IPC",
]

ROOT = abspath(dirname(__file__))
mbed_path = join(ROOT, "mbed-os")
TF_M_RELATIVE_PATH = (
    "platform/FEATURE_EXPERIMENTAL_API/FEATURE_PSA/TARGET_TFM/TARGET_TFM_V1_1"
)
sys.path.insert(0, mbed_path)
TF_M_BUILD_DIR = join(mbed_path, TF_M_RELATIVE_PATH, "TARGET_IGNORE")
POPEN_INSTANCE = None

from tools.targets import Target, TARGET_MAP, TARGET_NAMES


def are_dependencies_installed():
    def _is_cmake_installed():
        """
        Check if Cmake is installed
        :return: errorcode
        """
        command = ["cmake", "--version"]
        return run_cmd_and_return(command)

    def _is_make_installed():
        """
        Check if GNU Make is installed
        :return: errorcode
        """
        command = ["make", "--version"]
        return run_cmd_and_return(command)

    def _is_git_installed():
        """
        Check if git is installed
        :return: errorcode
        """
        command = ["git", "--version"]
        return run_cmd_and_return(command)

    def _is_srec_installed():
        """
        Check if srec_cat is installed
        :return: errorcode
        """
        command = ["srec_cat", "--version"]
        return run_cmd_and_return(command)

    def _is_mbedgt_installed():
        """
        Check if mbedgt is installed
        :return: errorcode
        """
        command = ["mbedgt", "--version"]
        return run_cmd_and_return(command)

    if _is_git_installed() != 0:
        logging.error('"git" is not installed. Exiting...')
        return -1
    elif _is_cmake_installed() != 0:
        logging.error('"Cmake" is not installed. Exiting...')
        return -1
    elif _is_make_installed() != 0:
        logging.error('"Make" is not installed. Exiting...')
        return -1
    elif _is_srec_installed() != 0:
        logging.error('"srec_cat" is not installed. Exiting...')
        return -1
    elif _is_mbedgt_installed() != 0:
        logging.error('"mbedgt" is not installed. Exiting...')
        return -1
    else:
        return 0


def run_cmd_and_return(command, output=False):
    """
    Run the command in the system and return either error code or output.
    Commands are passed as a list of tokens.
    E.g. The command 'git remote -v' would be passed in as:
     ['git', 'remote', '-v']

    :param command: System command as a list of tokens
    :param output: If set to True return output from child process
    :return: Return either output from child process or error code
    """

    global POPEN_INSTANCE
    with open(os.devnull, "w") as fnull:
        try:
            POPEN_INSTANCE = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=fnull
            )
        except FileNotFoundError:
            logging.error("Command not found: " + command[0])
            return -1

        std_out, __ = POPEN_INSTANCE.communicate()
        retcode = POPEN_INSTANCE.returncode
        POPEN_INSTANCE = None

        if output:
            return std_out.decode("utf-8")
        else:
            return retcode


def run_cmd_output_realtime(command, cmake_build_dir):
    """
    Run the command in the system and print output in realtime.
    Commands are passed as a list of tokens.
    E.g. The command 'git remote -v' would be passed in as:
     ['git', 'remote', '-v']

    :param command: System command as a list of tokens
    :param cmake_build_dir: Cmake build directory
    :return: Return the error code from child process
    """
    global POPEN_INSTANCE
    POPEN_INSTANCE = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cmake_build_dir,
    )
    for line in iter(POPEN_INSTANCE.stdout.readline, b""):
        logging.info(line.decode("utf-8").strip("\n"))

    POPEN_INSTANCE.communicate()
    retcode = POPEN_INSTANCE.returncode
    POPEN_INSTANCE = None
    return retcode


def check_and_clone_repo(name, deps, dir):
    """
    Check if the repositories are already cloned. If not clone them
    :param name: Name of the git repository
    :param deps: Dictionary containing dependency details
    :param dir: Directory to perform cloning
    """

    gitref = deps.get(name)[1]
    if not isdir(join(dir, name)):
        logging.info("Cloning %s repo", name)
        cmd = ["git", "-C", dir, "clone", "-b", gitref, deps.get(name)[0]]
        ret = run_cmd_and_return(cmd)
        if ret != 0:
            logging.critical("Failed to clone %s repo, error: %d", name, ret)
            sys.exit(1)

        logging.info("Cloned %s repo successfully", name)
    else:
        logging.info("%s repo exists, fetching latest...", name)
        cmd = ["git", "-C", join(dir, name), "fetch"]
        ret = run_cmd_and_return(cmd)
        if ret != 0:
            logging.critical(
                "Failed to fetch the latest %s, error: %d", name, ret
            )
            sys.exit(1)

        logging.info("Checking out %s...", gitref)
        # try gitref as a remote branch
        head = "origin/" + gitref
        cmd = ["git", "-C", join(dir, name), "checkout", head]
        ret = run_cmd_and_return(cmd)
        if ret != 0:
            logging.info(
                "%s is not a remote branch, trying %s directly", head, gitref
            )
            # gitref might be a tag or SHA1 which we checkout directly
            cmd = ["git", "-C", join(dir, name), "checkout", gitref]
            ret = run_cmd_and_return(cmd)
            if ret != 0:
                logging.critical(
                    "Failed to checkout %s, error: %d", gitref, ret
                )
                sys.exit(1)

        logging.info("Checked out %s successfully", gitref)


def exit_gracefully(signum, frame):
    """
    Crtl+C signal handler to exit gracefully
    :param signum: Signal number
    :param frame:  Current stack frame object
    """
    logging.info("Received signal %s, exiting..." % signum)
    global POPEN_INSTANCE
    try:
        if POPEN_INSTANCE:
            POPEN_INSTANCE.terminate()
            while not POPEN_INSTANCE.poll():
                continue
    except:
        pass

    sys.exit(0)


def get_tfm_secure_targets():
    """
    Creates a list of TF-M secure targets from Mbed OS targets.json.

    :return: List of TF-M secure targets.
    """
    return [str(t) for t in TARGET_NAMES if Target.get_target(t).is_TFM_target]


def get_tfm_regression_targets():
    """
    Creates a list of TF-M regression tests supported targets
    This parses the yaml file for supported target names and compares them
    with TF-M targets supported in Mbed OS

    :return: List of supported TF-M regression targets.
    """
    with open(join(dirname(__file__), "tfm_ns_import.yaml")) as ns_import:
        yaml_data = yaml.safe_load(ns_import)
        mbed_os_data = yaml_data["mbed-os"]
        tfm_regression_data = yaml_data["tf-m-regression"]

        regression_targets = list(
            set(get_tfm_secure_targets())
            & set(mbed_os_data)
            & set(tfm_regression_data)
        )

        return regression_targets
