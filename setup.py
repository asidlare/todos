import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt')) as f:
    requires = f.read()

with open(os.path.join(here, 'requirements_dev.txt')) as f:
    dev_requires = f.read()


setup(
    name='todos',
    version='0.1.0',
    description='todos',
    packages=find_packages(),
    install_requires=requires,
    extras_require={
        'dev': dev_requires
    },
    entry_points={
        'console_scripts': [
            'manage=scripts.manage:main',
            'run_tests=scripts.run_tests:main',
        ],
    },
)
