#! /usr/bin/env spack-python

import argparse
import os
import time
import spack.main
import spack.util.executable
from spack.util.path import canonicalize_path as spack_path_resolve

from datetime import date

import spack.environment as ev

today = date.today()
daystr = today.isoformat()

manager = spack.main.SpackCommand("manager")
env = spack.main.SpackCommand("env")
config = spack.main.SpackCommand("config")
concretize = spack.main.SpackCommand("concretize")
fetch = spack.main.SpackCommand("fetch")
spack_install = spack.main.SpackCommand("install")
module = spack.main.SpackCommand("module")
make = spack.util.executable.which("make")

parser = argparse.ArgumentParser()
parser.add_argument("--name", help="name of env for installing")
parser.add_argument("--pre-fetch",
                          help="fetch all the source code prior to install",
                          action="store_true"
                    )
parser.add_argument("--slurm-args",
                    help=(
                        "slurm argurments submitted as a single string. spaces will be split "
                        "and #SBATCH directives will be added before each argument")
                    )
parser.add_argument("--ranks", type=int)
parser.add_argument("--cdash", nargs='+', default=[], help="packages to run tests and submit to cdash")
parser.add_argument("--overwrite", action="store_true")
parser.add_argument("--depfile", action="store_true")


def get_env_name(args):
    _env_name = daystr
    if args.name:
        _env_name = args.name
    return _env_name


def environment_setup(args, env_name):
    out=manager("find-machine")
    project, machine = out.strip().split()
    template = os.path.expandvars("$EXAWIND_MANAGER/configs/{}/template.yaml".format(machine))

    if not os.path.isfile(template):
        template = os.path.expandvars("$EXAWIND_MANAGER/configs/base/template.yaml")

    if args.overwrite and ev.exists(env_name):
        env("rm", env_name, "-y")

    if not ev.exists(env_name):
        manager("create-env", "-n", env_name, "-y", template)

    print("Using env:", ev.read(env_name).path)


def configure_env(args, env_name):
    with ev.read(env_name) as e:
        config("add", "config:install_tree:{}".format(
               spack_path_resolve("$EXAWIND_MANAGER/opt/{}".format(e.name))
               ))
        config("add", "modules:default:tcl:all:suffixes:all:'{}'".format(e.name))
        if args.cdash:
            for pkg in args.cdash:
                config("add", "packages:{}:variants:\"{}\"".format(pkg,"+cdash_submit"))
        concretize("--force")
        if args.depfile:
            env("depfile", "-o", os.path.join(e.path, "Makefile"))
        if args.pre_fetch:
            fetch()

def make_args(env, ranks):
    args = [
        "-j{}".format(ranks),
        "SPACK_INSTALL_FLAGS='{}'".format("--show-log-on-error"),
    ]
    return args

def install(args, env_name):
    with ev.read(env_name) as e:
        os.chdir(e.path)
        if args.depfile:
            print("make",*make_args(e, args.ranks))
            make(*make_args(e, args.ranks))
        else:
            spack_install()

def create_slurm_file(args, env_name):
    e = ev.read(env_name)
    slurm_args = ["#SBATCH {}\n".format(a) for a in args.slurm_args.split()]
    with open(os.path.join(e.path, "submit.sh"), "w") as f:
        f.write("#!/bin/bash\n")

        for s in slurm_args:
            f.write(s)
        f.write("\n")

        if args.depfile:
            f.write("make " + " ".join(*make_args(e, args.ranks)+"\n"))
        else:
            f.write("\nsrun -N $SLURM_JOB_NUM_NODES -n {} spack -e {} install ".format(args.ranks, env_name))
        f.write("\nspack -e {} module tcl refresh -y".format(env_name))


def module_gen(args, env_name):
    with ev.read(env_name) as e:
        module("tcl", "refresh", "-y")


args = parser.parse_args()
env_name = get_env_name(args)
environment_setup(args, env_name)
print("configure args")
configure_env(args, env_name)
if args.slurm_args:
    print("create slurm args")
    create_slurm_file(args, env_name)
else:
    print("spack install")
    install(args, env_name)
    module_gen(args, env_name)
