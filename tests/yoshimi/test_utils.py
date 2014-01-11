import pytest
from tests.yoshimi import Mock
from yoshimi.utils import LazyPagination
from yoshimi.utils import page_number
from yoshimi.utils import Proxy


class TestPageNumber:
    def test_returns_one_for_negative_number(self):
        assert page_number(-1) == 1

    def test_returns_one_for_zero(self):
        assert page_number(0) == 1

    def test_returns_casts_to_int(self):
        assert page_number('2') == 2

    def test_return_number(self):
        assert page_number(5) == 5


class TestLazyPaginator:
    def test_calls_paginate_and_forwards_property(self):
        query = Mock()
        query.configure_mock(**{'paginate.return_value.total': 30})

        total = LazyPagination(query, 4).total

        query.paginate.assert_called_with(4)
        assert total == 30


class TestProxy:
    def test_calls_original_method(self):
        assert self._get_proxy().test() == 'test'

    def test_doesnt_calls_original_method(self):
        assert self._get_proxy().no_proxy() == 'proxy'

    def test_call_undefined_method(self):
        with pytest.raises(AttributeError):
            assert self._get_proxy().undefined() == 'proxy'

    def _get_proxy(self):
        class TestObject:
            def test(self):
                return 'test'

        class Cut(Proxy):
            def __init__(self):
                self._proxy = TestObject()

            def no_proxy(self):
                return 'proxy'

        return Cut()


class TestCacheFunc:
    def test_func_only_called_once(self):
        from yoshimi.utils import cache_func
        func = test.Mock()
        func.return_value = 'string'
        new_func = cache_func(func)
        rv = new_func()
        rv2 = new_func()

        func.assert_called_once_with()
        assert rv == 'string'
        assert rv2 == 'string'
