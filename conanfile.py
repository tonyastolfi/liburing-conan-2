from conan import ConanFile
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.tools.layout import basic_layout
from conan.tools.files import get, patch, chdir, rmdir, copy
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration
import os

required_conan_version = ">=1.33.0"


class LiburingConan(ConanFile):
    name = "liburing"
    version = "2.4"
    license = "GPL-2.0-or-later"
    homepage = "https://github.com/axboe/liburing"
    url = "https://github.com/conan-io/conan-center-index"
    description = ("helpers to setup and teardown io_uring instances, and also a simplified interface for "
                   "applications that don't need (or want) to deal with the full kernel side implementation.")
    topics = ("asynchronous-io", "async", "kernel")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "with_libc": [True, False],
    }
    default_options = {
        "fPIC": True,
        "shared": False,
        "with_libc": True,
    }

    exports_sources = ["patches/*"]

    _autotools = None


    def layout(self):
        basic_layout(self, src_folder="source")
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if Version(self.version) < "2.2":
            del self.options.with_libc

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def _configure_args(self):
        args = []
        if self.options.get_safe("with_libc") == False:
            args.append("--nolibc")
        return args
        
    def generate(self):
        deps_tc = AutotoolsDeps(self)
        deps_tc.generate()

        tc = AutotoolsToolchain(self)
        tc.configure_args = self._configure_args()
        tc.cflags.append("-std=gnu99")
        tc.generate()

        
    def requirements(self):
        #self.requires("linux-headers-generic/5.13.9")
        return

    def validate(self):
        # FIXME: use kernel version of build/host machine.
        # kernel version should be encoded in profile
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                "liburing is supported only on linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        self._autotools = Autotools(self)
        self._autotools.configure(args=self._configure_args())
        return self._autotools

    def _patch_sources(self):
        for data in self.conan_data.get("patches", {}).get(self.version, []):
            patch(self, **data)

    def build(self):
        self._patch_sources()
        with chdir(self, self.source_folder):
            autotools = self._configure_autotools()
            autotools.make()

    def package(self):
        copy(self, "COPYING*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        with chdir(self, self.source_folder):
            autotools = self._configure_autotools()
            install_args = [
                "ENABLE_SHARED={}".format(1 if self.options.shared else 0)
            ]
            autotools.install(args=install_args)

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "man"))

        if self.options.shared:
            os.remove(os.path.join(self.package_folder, "lib", "liburing.a"))

    def package_info(self):
        self.cpp_info.names["pkg_config"] = "liburing"
        self.cpp_info.libs = ["uring"]

