from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.scm import Version
import platform
import re
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def layout(self):
        cmake_layout(self)

    @property
    def _sufficient_linux_kernel_version(self):
        # FIXME: use kernel version of build/host machine. kernel version should be encoded in profile
        linux_kernel_version = re.match("([0-9.]+)", platform.release()).group(1)
        return Version(linux_kernel_version) >= "5.1"

    def test(self):
        if not cross_building(self) and self._sufficient_linux_kernel_version:
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)
