from setuptools import find_packages, setup

setup(
    name='waad',
    version='0.1.0',
    author='Sia Partners',
    author_email='alexandre.levesque@sia-partners.com',
    packages=find_packages(),
    package_dir={'waad': 'waad'},
    include_package_data=True,       
    python_requires='>=3.7',
    description='A package implementing scripts for cybersecurity purposes',
)