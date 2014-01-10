# flake8: noqa
import os

try:  # python >= 3.3
    from unittest.mock import Mock, MagicMock, patch
except ImportError:  # to support python <= 3.2
    from mock import Mock, MagicMock, patch

import pytest
from yoshimi.test.cases import DatabaseTestCase
from yoshimi.test.cases import QueryCountTestCase

all_databases = pytest.mark.all_databases


if not 'YOSHIMI_TEST_DB' in os.environ:
    os.environ['YOSHIMI_TEST_DB'] = 'sqlite:///:memory:'
