from pyramid.view import view_config
from yoshimi.views import index

def includeme(config):
    pass
    #config.add_route('y_index', '*path', renderer='frontend/index.mako', view=index)
