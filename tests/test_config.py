from pyramid.config import Configurator

from yoshimi import test
from yoshimi.interfaces import IQueryExtensions
from yoshimi.config import add_query_directive


class ConfigTest:
    def _makeConfig(*args, **kwargs):
        config = Configurator(*args, **kwargs)
        return config

    def test_add_query_directive(self):
        config = Configurator(autocommit=True)
        callable = lambda x: None

        add_query_directive(config, 'foo', callable)

        exts = config.registry.getUtility(IQueryExtensions)
        assert 'foo' in exts.methods
