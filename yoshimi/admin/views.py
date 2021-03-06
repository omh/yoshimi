from yoshimi import views
from yoshimi.utils import (
    run_once,
    page_number,
    LazyPagination,
)
from yoshimi.url import redirect_back


layout_views = [
    lambda _, req: {'trash_count': run_once(req.y_repo.trash.count)}
]


@views.merge(views.index, *layout_views)
def index(context, request):
    return {}


@views.merge(*layout_views)
def trash_index(_, request):
    def can_select(trash_content):
        if not trash_content.content.parent:
            return False
        return trash_content.content.parent.is_available

    trash_contents = LazyPagination(
        request.y_repo.trash.items(),
        page_number(request.GET.get('page', 1))
    )

    return {
        'trash_contents': trash_contents,
        'can_select': can_select,
    }


def trash_empty(request):
    request.y_repo.trash.empty()
    return redirect_back(
        request, fallback=request.route_url('y.admin.trash.index')
    )


def trash_restore(request):
    ids = request.POST.getall('trash_item_id')
    request.y_repo.trash.restore(ids)
    return redirect_back(
        request, fallback=request.route_url('y.admin.trash.index')
    )
