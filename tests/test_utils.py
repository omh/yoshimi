from yoshimi import test
from yoshimi.utils import LazyPagination
from yoshimi.utils import page_number
from yoshimi.utils import Proxy


class TestPageNumber(test.TestCase):
    def test_returns_one_for_negative_number(self):
        self.assertEquals(page_number(-1), 1)

    def test_returns_one_for_zero(self):
        self.assertEquals(page_number(0), 1)

    def test_returns_casts_to_int(self):
        self.assertEquals(page_number('2'), 2)

    def test_return_number(self):
        self.assertEquals(page_number(5), 5)


class TestLazyPaginator(test.TestCase):
    def test_calls_paginate_and_forwards_property(self):
        query = test.Mock()
        query.configure_mock(**{'paginate.return_value.total': 30})

        total = LazyPagination(query, 4).total

        query.paginate.assert_called_with(4)
        self.assertEqual(total, 30)


class TestProxy(test.TestCase):
    def test_calls_original_method(self):
        self.assertEqual(self._get_proxy().test(), 'test')

    def test_doesnt_calls_original_method(self):
        self.assertEqual(self._get_proxy().no_proxy(), 'proxy')

    def test_call_undefined_method(self):
        with self.assertRaises(AttributeError):
            self.assertEqual(self._get_proxy().undefined(), 'proxy')

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
