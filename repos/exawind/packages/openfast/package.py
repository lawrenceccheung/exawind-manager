# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack.pkg.builtin.openfast import Openfast as bOpenfast

class Openfast(bOpenfast):
    patch("hub_seg_fault.patch", when="@2.7:3.2")
    patch("segfault_message.patch", when="%clang@12.0.1 build_type=RelWithDebInfo")
    patch("openmp.patch", when="@develop")
    version("3.5.3", tag="v3.5.3", commit="6a7a543790f3cad4a65b87242a619ac5b34b4c0f")
    version("fsi", git="https://github.com/gantech/openfast.git", branch="f/br_fsi_2")

    variant("rosco", default=False,
            description="Build ROSCO controller alongside OpenFAST")

    depends_on("rosco", when="+rosco")
    depends_on("netcdf-c", when="@fsi")
    depends_on("yaml-cpp@0.6.0:0.6.3", when="+cxx")

