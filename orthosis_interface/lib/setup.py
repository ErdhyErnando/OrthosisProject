import setuptools

setuptools.setup(
    include_package_data=True,
    name='orthosis_lib',
    version='0.1.0',
    description='orthosis_lib',
    url='https://git.hb.dfki.de/dfki_ude/orthosis_interface',
    author='DFKI',
    packages=setuptools.find_packages(),
    install_requires=[
        'matplotlib',
        'numpy',
        'setuptools',
        'SharedArray',
        'mini-cheetah-motor-driver-socketcan',
        'pyserial', 
        'scipy'
    ],
    classifiers=["Programming langugage :: Python :: Version > 3.6",
                 "Operating System :: OS independent"],
)


