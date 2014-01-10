from yoshimi import test


class TestTemplateFilters:
    def setup(self):
        self.context = test.Mock()
        self.request_mock = test.Mock()
        self.request_mock.path_qs = '/a'

        get_request_mock = test.patch('yoshimi.templating.get_current_request')
        self.get_request_mock = get_request_mock.start()
        self.get_request_mock.return_value = self.request_mock

    def teardown(self):
        test.patch.stopall()

    @test.patch('yoshimi.templating.url', autospec=True)
    def test_url_filter(self, url_mock):
        from yoshimi.templating import url_filter
        url_filter(self.context, 'a', b='c')

        url_mock.assert_called_once_with(
            self.request_mock,
            self.context,
            'a',
            b='c',
        )

    @test.patch('yoshimi.templating.url', autospec=True)
    def test_url_back_filter(self, url_mock):
        from yoshimi.templating import url_back_filter
        url_back_filter(self.context, 'a', b='c')

        url_mock.assert_called_once_with(
            self.request_mock,
            self.context,
            'a',
            b='c',
            query={'back': '/a'}
        )

    @test.patch('yoshimi.templating.path', autospec=True)
    def test_path_filter(self, path_mock):
        from yoshimi.templating import path_filter
        path_filter(self.context, 'a', b='c')

        path_mock.assert_called_once_with(
            self.request_mock,
            self.context,
            'a',
            b='c',
        )

    @test.patch('yoshimi.templating.path', autospec=True)
    def test_path_back_filter(self, path_mock):
        from yoshimi.templating import path_back_filter
        path_back_filter(self.context, 'a', b='c')

        path_mock.assert_called_once_with(
            self.request_mock,
            self.context,
            'a',
            b='c',
            query={'back': '/a'}
        )
