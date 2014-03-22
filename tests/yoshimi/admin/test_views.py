from tests.yoshimi import (
    Mock,
    patch
)
from yoshimi.admin.views import (
    index,
    trash_empty,
    trash_index,
)


class TestIndex:
    def test_index(self):
        assert index(Mock(), Mock()) == {}


class TestTrashIndex:
    def setup(self):
        LazyPagination = patch(
            'yoshimi.admin.views.LazyPagination', autospec=True
        )
        self.lazy_pagination = LazyPagination.start()

        page_number = patch('yoshimi.admin.views.page_number', autospec=True)
        self.page_number = page_number.start()

    def teardown(self):
        patch.stopall()

    def test_can_not_select_without_parent(self):
        trash_content = Mock()
        trash_content.content.parent = None
        rv = trash_index(Mock(), Mock())

        assert rv['can_select'](trash_content) is False

    def test_can_not_select_without_available_parent(self):
        trash_content = Mock()
        trash_content.content.parent.is_available = False
        rv = trash_index(Mock(), Mock())

        assert rv['can_select'](trash_content) is False

    def test_can_select_when_have_parent_and_is_available(self):
        trash_content = Mock()
        trash_content.content.parent.is_available = True
        rv = trash_index(Mock(), Mock())

        assert rv['can_select'](trash_content) is True

    def test_returns_trash_contents(self):
        request = Mock()
        trash_contents = Mock()
        self.lazy_pagination.return_value = trash_contents

        rv = trash_index(Mock(), request)

        request.y_repo.trash.items.assert_called_once_with()
        assert rv['trash_contents'] == trash_contents


class TestTrashEmpty:
    @patch('yoshimi.admin.views.redirect_back')
    def test_trash_empty(self, redirect_back):
        redirect_back.return_value = '/return'
        request = Mock()
        request.route_url.return_value = '/redir'
        rv = trash_empty(request)

        assert rv == '/return'
        request.y_repo.trash.empty.assert_called_once_with()
        redirect_back.assert_called_once_with(request, fallback='/redir')
