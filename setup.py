import os
import glob
import os.path as osp
from itertools import product
from setuptools import setup, find_packages

import torch
from torch.utils.cpp_extension import BuildExtension
from torch.utils.cpp_extension import CppExtension, CUDAExtension, CUDA_HOME

WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
suffices = ['cpu', 'cuda'] if WITH_CUDA else ['cpu']
if os.getenv('FORCE_CUDA', '0') == '1':
    suffices = ['cuda']
if os.getenv('FORCE_CPU', '0') == '1':
    suffices = ['cpu']

BUILD_DOCS = os.getenv('BUILD_DOCS', '0') == '1'


def get_extensions():
    extensions = []

    extensions_dir = osp.join(osp.dirname(osp.abspath(__file__)), 'csrc')
    main_files = glob.glob(osp.join(extensions_dir, '*.cpp'))

    for main, suffix in product(main_files, suffices):
        define_macros = []
        extra_compile_args = {'cxx': ['-O2']}
        extra_link_args = ['-s']

        if suffix == 'cuda':
            define_macros += [('WITH_CUDA', None)]
            nvcc_flags = os.getenv('NVCC_FLAGS', '')
            nvcc_flags = [] if nvcc_flags == '' else nvcc_flags.split(' ')
            nvcc_flags += ['-arch=sm_35', '--expt-relaxed-constexpr', '-O2']
            extra_compile_args['nvcc'] = nvcc_flags

        name = main.split(os.sep)[-1][:-4]
        sources = [main]

        path = osp.join(extensions_dir, 'cpu', f'{name}_cpu.cpp')
        if osp.exists(path):
            sources += [path]

        path = osp.join(extensions_dir, 'cuda', f'{name}_cuda.cu')
        if suffix == 'cuda' and osp.exists(path):
            sources += [path]

        Extension = CppExtension if suffix == 'cpu' else CUDAExtension
        extension = Extension(
            f'torch_spline_conv._{name}_{suffix}',
            sources,
            include_dirs=[extensions_dir],
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
        )
        extensions += [extension]

    return extensions


install_requires = []
setup_requires = ['pytest-runner']
tests_require = ['pytest', 'pytest-cov']

setup(
    name='torch_spline_conv',
    version='1.2.0',
    author='Matthias Fey',
    author_email='matthias.fey@tu-dortmund.de',
    url='https://github.com/rusty1s/pytorch_spline_conv',
    description=('Implementation of the Spline-Based Convolution Operator of '
                 'SplineCNN in PyTorch'),
    keywords=[
        'pytorch',
        'geometric-deep-learning',
        'graph-neural-networks',
        'spline-cnn',
    ],
    license='MIT',
    python_requires='>=3.6',
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    ext_modules=get_extensions() if not BUILD_DOCS else [],
    cmdclass={
        'build_ext': BuildExtension.with_options(no_python_abi_suffix=True)
    },
    packages=find_packages(),
)
