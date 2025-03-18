from setuptools import setup
from Cython.Build import cythonize

setup(
    # ext_modules=cythonize("pseudo_fslab.pyx", compiler_directives={'language_level': '3'})
    # ext_modules=cythonize("check_list.pyx", compiler_directives={'language_level': '3'})
    # ext_modules=cythonize("check_slab.pyx", compiler_directives={'language_level': '3'})
    # ext_modules=cythonize("check_cache.pyx", compiler_directives={'language_level': '3'})
)
