# -*- coding: utf-8 -*-
#
# murderrl documentation build configuration file, created by
# sphinx-quickstart on Thu Mar  3 22:57:26 2011.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import inspect

from sphinx.ext.autodoc import ClassDocumenter

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.append(os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.autosummary']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'murderrl'
copyright = u'2011, Jon McManus, Johanna Ploog'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.0a'
# The full version, including alpha/beta/rc tags.
release = '0.0a'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['.build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'murderrldoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'murderrl.tex', u'murderrl Documentation',
   u'Jon McManus, Johanna Ploog', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

autodoc_member_order = "groupwise"

autoclass_content = "class"

def method_info (method):
    if inspect.ismethod(method):
        return "%s.%s" % (method.im_class.__name__, method.im_func.__name__)
    return "%s" % (method.__name__)

def _resolve_doc (method):
    my_docs = []

    if hasattr(method, "extends"):
        extends = method.extends
        if isinstance(extends, tuple):
            for exmeth in extends:
                assert inspect.ismethod(exmeth)
                doc = _resolve_doc(exmeth)
                if doc:
                    my_docs.extend(doc)
        else:
            my_docs.extend(_resolve_doc(extends))
    elif method.__doc__:
        my_docs.append((method_info(method), inspect.getdoc(method)))

    return my_docs

def resolve_doc (method):
    lines = _resolve_doc(method)
    result = []

    done_methods = []

    for method, line in lines:
        if method in done_methods:
            continue

        result.append("*Documentation inherited from* :meth:`%s`:" % (method))
        result.append("")
        result.extend(line.split("\n"))
        done_methods.append(method)

    return result

def process_signature (app, what, name, obj, options, signature, return_annotation):
    if hasattr(obj, "extends") and callable(obj):
        extends = obj.extends
        if isinstance(extends, tuple):
            argspec = inspect.getargspec(extends[0])
        else:
            argspec = inspect.getargspec(extends)

        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]

        signature = inspect.formatargspec(*argspec)

    return (signature, return_annotation)

def process_docstring (app, what, name, obj, options, lines):
    if hasattr(obj, "extends") and callable(obj):
        lines.extend(resolve_doc(obj))

    return lines

class NewClassDocumenter(ClassDocumenter):
    def format_args(self):
        # for classes, the relevant signature is the __init__ method's
        initmeth = self.get_attr(self.object, '__init__', None)
        # classes without __init__ method, default __init__ or
        # __init__ written in C?
        if initmeth is None or initmeth is object.__init__ or not \
               (inspect.ismethod(initmeth) or inspect.isfunction(initmeth)):
            return None
        try:
            argspec = inspect.getargspec(initmeth)
        except TypeError:
            # still not possible: happens e.g. for old-style classes
            # with __init__ in C
            return None

        if argspec[0] and argspec[0][0] in ('cls', 'self'):
            del argspec[0][0]

        args = inspect.formatargspec(*argspec)

        result = self.env.app.emit_firstresult(
            'autodoc-process-signature', self.objtype, self.fullname,
            initmeth, self.options, args, None)

        if result:
            return result[0]
        else:
            return args

def setup (app):
    app.add_autodocumenter(NewClassDocumenter)
    app.connect('autodoc-process-docstring', process_docstring)
    app.connect('autodoc-process-signature', process_signature)
