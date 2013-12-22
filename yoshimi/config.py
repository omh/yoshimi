from yoshimi.interfaces import IQueryExtensions
from yoshimi.repo import _QueryExtensions


def add_query_directive(config, name=None, callable=None):
    callable = config.maybe_dotted(callable)

    def register():
        exts = config.registry.queryUtility(IQueryExtensions)
        if exts is None:
            exts = _QueryExtensions()
            config.registry.registerUtility(exts, IQueryExtensions)
        exts.methods[name] = callable

    intr = config.introspectable(
        'yoshimi query extensions',
        name,
        config.object_description(callable),
        'query',
    )
    intr['callable'] = callable
    intr['name'] = name

    config.action(
        ('yoshimi query extensions', name),
        callable=register,
        introspectables=(intr,),
    )
