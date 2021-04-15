# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# os.path.join(os.path.pardir, os.path.pardir) is equivalent to '../..', ie go twice to the
# parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.pardir, os.path.pardir)))
# sys.path.insert(0, os.path.abspath(os.path.pardir))
# sys.path.append('/waad/waad')



# -- Project information -----------------------------------------------------

project = 'WAAD'
copyright = '2020, Alexandre LEVESQUE & Nicolas Guinard'
author = 'Alexandre LEVESQUE & Nicolas Guinard'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.inheritance_diagram',
    'sphinxcontrib.napoleon',
    'sphinx.ext.autosummary',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------

# autodoc
autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = False

autodoc_default_options = {
    'private-members': True,
    'show-inheritance': True,
    'undoc-members': True,
    'exclude-members': '__weakref__, __dict__, __module__, __hash__, __annotations__',
}

# to do extension
todo_include_todos = True

# napoleon
napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True

html_favicon='logo_anssi.ico'

nbsphinx_execute = 'never'

# set path to doctest generated figures
doctest_global_setup = '''
import numpy as np

np.random.seed(42)

DOCTEST_FIGURES_PATH = 'source/_static/doctest_figures'
'''

autosummary_generate = True
autosummary_imported_members = True

add_module_names = False