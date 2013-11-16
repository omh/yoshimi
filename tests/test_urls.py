from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPMovedPermanently
from yoshimi import test
from yoshimi import url


class TestExtractSlugFrom(test.TestCase):
    def setUp(self):
        self.valid_urls = [
            ('/Wins-Champions-League-28', '/Wins-Champions-League-28'),
            ('/News/Sports-28/Arsenal', '/News/Sports-28'),
            ('/News-12/Sports-28/Arsenal', '/News-12/Sports-28'),
            ('/News-28','/News-28'),
            ('News-28', 'News-28'),
            ('28','28'),
        ]
        self.invalid_urls = [
            '/',
            '/News/Sports/'
            '/News/Sports-aa/',
            '/News/Sports28',
            '/News/Sports_28',
        ]

    def test_valid_urls(self):
        for valid_url, valid_slug in self.valid_urls:
            id, slug = url.extract_slug_from(valid_url.split("/"))
            self.assertEqual(28, id, "Id from url %s should be 28" % valid_url)
            self.assertEqual(valid_slug, slug, "Slug should be '%s'" % valid_slug)

    def test_invalid_urls(self):
        for invalid_url in self.invalid_urls:
            id, slug = url.extract_slug_from(invalid_url.split("/"))
            self.assertIsNone(id, "Id of url '%s' should be none" % invalid_url)


class TestGenerateSlug(test.TestCase):
    def setUp(self):
        from yoshimi.content import Content
        self.location = test.Mock()
        self.location.slugs = ['Test', 'Slug']
        self.location.id = 5

        self.obj = test.Mock(spec=Content)

    def test_content_type_no_parent(self):
        self.obj.main_location = self.location
        slug = url.generate_slug(self.obj)
        self.assertEqual(slug, "Test/Slug-5")

    def test_content_type_with_parent(self):
        self.obj.location_for_parent.return_value = self.location
        slug = url.generate_slug(self.obj, parent=self.location)
        self.assertEqual(slug, "Test/Slug-5")


class TestUrl(test.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.req = test.Mock()
        self.req.matched_route.name = 'route_name'

        self.location = test.Mock()
        self.location.slugs = ['Test', 'Slug']
        self.location.id = 5

    def tearDown(self):
        testing.tearDown()

    def test_url_with_default_route(self):
        self.req.route_path.return_value = "/Test/Path"
        u = url.url(self.req, self.location)
        self.assertEqual("/Test/Path", u)
        self.req.route_path.assert_called_with(
            'route_name', traverse='Test/Slug-5', _query={}
        )

    def test_url_with_elements(self):
        url.url(self.req, self.location, 'edit')
        self.req.route_path.assert_called_with(
            'route_name', traverse=('Test', 'Slug-5', 'edit'), _query={}
        )

    def test_url_with_query_params(self):
        url.url(self.req, self.location, q1='testing')
        self.req.route_path.assert_called_with(
            'route_name', traverse='Test/Slug-5', _query={'q1': 'testing'}
        )


class TestRedirectIfSlugMismatch(test.TestCase):
    def setUp(self):
        self.req = test.Mock()

    def _fut(self):
        from yoshimi.url import redirect_if_slug_mismatch
        return redirect_if_slug_mismatch

    def test_return_none_when_slug_matches(self):
        self.assertIsNone(self._fut()(self.req, "/a", "/a"))

    def test_raise_redirect_when_slug_mismatch(self):
        self.req.route_path.return_value = '/admin/somewhere'
        with self.assertRaises(HTTPMovedPermanently) as redir:
            self._fut()(self.req, '/a', '/b')
            self.assertEqual('/admin/somewhere', redir.location)


class TestLineageForRequest(test.TestCase):
    def setUp(self):
        self.req = testing.DummyRequest()

    def test_location_not_found(self):
        with self.assertRaises(HTTPNotFound):
            url.lineage_for_request(self.req)

    def test_raises_redirect_when_slug_does_not_match(self):
        with test.patch('yoshimi.url.extract_slug_from') as extract_slug_mock, \
             test.patch('yoshimi.url.locations_for_id') as locations_for_id_mock, \
             test.patch('yoshimi.url.generate_slug') as generate_slug_mock, \
             test.patch('yoshimi.url.redirect_if_slug_mismatch') as redirect_if:
            extract_slug_mock.return_value = (5, '/testing')
            locations_for_id_mock.return_value = [1,2,3]
            generate_slug_mock.return_value = '/SomeSlug'
            redirect_if.side_effect = HTTPMovedPermanently(location='/testing')

            with self.assertRaises(HTTPMovedPermanently):
                url.lineage_for_request(self.req)

    def test_returns_correct_linage(self):
        with test.patch('yoshimi.url.extract_slug_from') as extract_slug_mock, \
             test.patch('yoshimi.url.locations_for_id') as locations_for_id_mock, \
             test.patch('yoshimi.url.generate_slug') as generate_slug_mock:
            extract_slug_mock.return_value = (5, '/testing')
            locations_for_id_mock.return_value = [1,2,3]
            generate_slug_mock.return_value = '/testing'

            rv = url.lineage_for_request(self.req)
            self.assertEqual(rv, [1,2,3])


class TestMakeTree(test.TestCase):
    def test_returns_none_if_empty(self):
        self.assertIsNone(url.make_tree([]))

    def test_returns_tree_with_root_first(self):
        from yoshimi.content import Location
        root = test.Mock()
        child1 = test.Mock() 
        child2 = test.Mock() 

        tree_root = url.make_tree([root, child1, child2])

        self.assertEqual(tree_root._child, root)
        self.assertEqual(tree_root._child._child, child1)
        self.assertEqual(tree_root._child._child._child, child2)
        self.assertEqual(child2.__parent__.__parent__, root)
