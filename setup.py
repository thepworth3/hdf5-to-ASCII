from setuptools import setup, find_packages

setup(
    name='nxs_to_ascii',
    version='1.0.0',
    author='Thomas Hepworth',
    description='Extract datasets from NeXus/HDF5 files and export to CSV',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/<your-username>/nxs_to_ascii',
    packages=find_packages(),
    install_requires=[
        'h5py',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'nxs_to_ascii=nxs_to_ascii.nxs_to_ascii:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)
