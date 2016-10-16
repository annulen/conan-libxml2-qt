from conans import ConanFile, ConfigureEnvironment
import os
from conans.tools import download, unzip, replace_in_file

class LibxmlConan(ConanFile):
    name = "libxml2"
    version = "2.9.4"
    url = "http://github.com/vitallium/conan-libxml2-qt"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake", "txt"
    src_dir = "libxml2-%s" % version
    license = "https://git.gnome.org/browse/libxml2/tree/Copyright"

    def source(self):
        zip_name = "libxml2-%s.zip" % self.version
        url = "https://git.gnome.org/browse/libxml2/snapshot/%s" % zip_name
        download(url, zip_name)
        unzip(zip_name)
        os.unlink(zip_name)

    def configure(self):
        if self.settings.compiler == "Visual Studio" and \
           self.options.shared and "MT" in str(self.settings.compiler.runtime):
            self.options.shared = False
            self.configure_options = "iconv=no xinclude=no \
             valid=no xptr=no c14n=no \
             catalog=no regexps=no \
             zlib=no lzma=no \
             schemas=no schematron=no \
             threads=no legacy=no"
        else:
            self.configure_options = "--without-python \
             --without-valid \
             --without-xinclude \
             --without-xptr \
             --without-c14n \
             --without-catalog \
             --without-regexps \
             --without-zlib \
             --without-lzma \
             --without-schemas \
             --without-schematron \
             --without-threads \
             --without-legacy \
             "
            if self.options.shared:
                self.configure_options += "--disable-static --enable-shared"
            else:
                self.configure_options += "--enable-static --disable-shared"

    def build(self):
        if self.settings.os == "Windows":
            self.build_windows()
        else:
            self.build_with_configure()
    
    def build_windows(self):
        self.run('cd %s\win32 && cscript configure.js cruntime=/%s %s' % (
            self.src_dir,
            self.settings.compiler.runtime,
            self.configure_options
            ))
        self.run("cd %s\\win32 && nmake /f Makefile.msvc" % self.src_dir)

    def build_with_configure(self):
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)
        self.run("cd %s && chmod +x ./autogen.sh && %s ./autogen.sh --prefix=%s %s" % (
            self.src_dir,
            env.command_line,
            self.package_folder,
            self.configure_options
            ))
        self.run("cd %s && %s make -j5" % (self.src_dir, env.command_line))
        self.run("cd %s &&%s make install" % (self.src_dir, env.command_line))

    def package(self):
        if self.settings.os != "Windows":
            return

        self.copy("*.h", "include", src=self.src_dir, keep_path=True)
        self.copy(pattern="*.dll", dst="bin", src=self.src_dir, keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src=self.src_dir, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["libxml2"]

    def compose_msvc_path(self, paths):
        return ";".join("%s" % p.replace("\\", "/") for p in paths)