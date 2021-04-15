from setuptools import find_packages, setup

setup(
    name='ad_tree',
    version='0.1.0',
    author='Sia Partners',
    author_email='alexandre.levesque@sia-partners.com',
    packages=find_packages(),
    package_dir={'ad_tree': 'ad_tree'},
    include_package_data=True,       
    python_requires='>=3.7',
    description='A package implementing adtree inspired https://github.com/uraplutonium/adtree-py',
)
