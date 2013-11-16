from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource
from css.pure import pure
from js.jquery import jquery

library = Library('yoshimi_admin', 'static', minifiers={'.js': 'jsmin'})

js = Group([
    jquery,
    Resource(library, 'js/lib/tree.jquery.js'),
    Resource(library, 'js/admin.js'),
])

css = Group([
    pure,
    Resource(library, 'css/main.css', compiler='sass', source='css/main.scss'),
])
