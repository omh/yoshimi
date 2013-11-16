try:
    from mock import Mock, MagicMock, patch
except ImportError:
    from unittest.mock import Mock, MagicMock, patch

from nose.plugins.attrib import attr
from yoshimi.test.cases import TestCase
from yoshimi.test.cases import DatabaseTestCase

all_databases = attr('database')
