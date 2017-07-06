from conans import ConanFile, ConfigureEnvironment
import os, codecs, re
from conans.tools import download, untargz, cpu_count, os_info

class LibxmlConan(ConanFile):
    name = "libxml2"
    version = "2.9.4"
    url = "http://github.com/vitallium/conan-libxml2-qt"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    src_dir = "libxml2-%s" % version
    license = "https://git.gnome.org/browse/libxml2/tree/Copyright"
    requires = "icu/59.1@vitallium/stable"

    def source(self):
        tar_name = "libxml2-%s.tar.gz" % self.version
        url = "http://xmlsoft.org/sources/" + tar_name
        download(url, tar_name)
        untargz(tar_name)
        os.unlink(tar_name)

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            if self.options.shared and "MT" in str(self.settings.compiler.runtime):
                self.options.shared = False

            self.configure_options = "python=no \
                icu=yes \
                iconv=no \
                valid=no \
                xinclude=no \
                xptr=no \
                c14n=no \
                catalog=no \
                regexps=no \
                zlib=no \
                lzma=no \
                schemas=no \
                schematron=no \
                threads=no \
                legacy=no \
                ftp=no \
                http=no \
                "
        else:
            self.configure_options = "--without-python \
             --with-icu \
             --without-iconv \
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
             --without-ftp \
             --without-http \
             "
            if self.options.shared:
                self.configure_options += "--disable-static --enable-shared"
            else:
                self.configure_options += "--enable-static --disable-shared"

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self.build_windows()
        else:
            self.build_with_configure()

    def build_windows(self):
        # taken from: https://github.com/lasote/conan-libxml2/blob/master/conanfile.py#L38
        icu_headers_paths = self.deps_cpp_info["icu"].include_paths[0]
        icu_lib_paths= " ".join(['lib="%s"' % lib for lib in self.deps_cpp_info["icu"].lib_paths])
        icu_libs = self.deps_cpp_info["icu"].libs

        # use the correct icu libs
        makefile_win_path = os.path.join(self.src_dir, "win32", "Makefile.msvc")
        encoding = self.detect_by_bom(makefile_win_path, "utf-8")
        patched_content = self.load(makefile_win_path, encoding)
        patched_content = re.sub("icu.lib", " ".join("%s.lib"%i for i in icu_libs), patched_content)
        self.save(makefile_win_path, patched_content)

        self.run('cd %s\win32 && cscript configure.js cruntime=/%s include=\"%s\" %s %s' % (
            self.src_dir,
            self.settings.compiler.runtime,
            icu_headers_paths,
            icu_lib_paths,
            self.configure_options,
            ))
        self.run("cd %s\\win32 && nmake /f Makefile.msvc" % self.src_dir)

    def normalize_prefix_path(self, p):
        if os_info.is_windows:
            return p.replace('\\', '/')
        else:
            return p

    def build_with_configure(self):
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)
        command_env = env.command_line_env
        if os_info.is_windows:
            command_env += " &&"
            libflags = " ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs])
            command_env += ' set "LIBS=%s" &&' % libflags

        self.run("%s sh %s/configure --prefix=%s %s" % (
            command_env,
            self.src_dir,
            self.normalize_prefix_path(self.package_folder),
            self.configure_options
            ))
        self.run("%s make -j %s" % (command_env, cpu_count()))
        self.run("%s make install" % command_env)

    def package(self):
        if self.settings.os != "Windows":
            return

        include_path = os.path.join(self.src_dir, "include")
        self.copy("*.h", "include", src=include_path, keep_path=True)
        self.copy(pattern="*.dll", dst="bin", src=self.src_dir, keep_path=False)
        self.copy(pattern="*.lib", dst="lib", src=self.src_dir, keep_path=False)

    def package_info(self):
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs = ["libxml2"]
        else:
            self.cpp_info.libs = ["xml2"]

    def compose_msvc_path(self, paths):
        return ";".join("%s" % p.replace("\\", "/") for p in paths)

    # from https://github.com/SteffenL/conan-wxwidgets-custom/blob/master/conanfile.py#L260
    def load(self, path, encoding=None):
        encoding = detect_by_bom(path, "utf-8") if encoding is None else encoding
        with codecs.open(path, "rb", encoding=encoding) as f:
            return f.read()

    def save(self, path, content, encoding=None):
        with codecs.open(path, "wb", encoding=encoding) as f:
            f.write(content)

    # Ref.: http://stackoverflow.com/a/24370596
    def detect_by_bom(self,path,default):
        with open(path, 'rb') as f:
            raw = f.read(4)    #will read less if the file is smaller
        for enc,boms in \
                ('utf-8-sig',(codecs.BOM_UTF8,)),\
                ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
                ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
            if any(raw.startswith(bom) for bom in boms): return enc
        return default