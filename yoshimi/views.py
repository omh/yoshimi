"""
    yoshimi.views
    ~~~~~~~~~

    This module provides all the views that make up Yoshimi.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps
import venusian
from yoshimi.browse import BrowsePolicy
from yoshimi.content import Content
from yoshimi.forms import (
    LoginForm,
    ContentEditForm,
    ContentMoveForm,
)
from yoshimi.url import (
    redirect_back,
    redirect_back_to_context,
    redirect_back_to_parent,
)
from yoshimi.utils import (
    page_number,
    LazyPagination
)


def index(context, request):
    children = LazyPagination(
        request.y_repo.query(context).children().load_path(),
        page_number(request.GET.get('page', 1))
    )

    return {
        'children': children,
        'can_move': bool(context.parent)
    }


# @TODO: Not tested properly - was erroring out on request.context.content
# which doesn't exists anymore
def edit(context, request):
    form = ContentEditForm.from_request(request)
    if request.method == 'POST' and form.validate():
        form.populate_obj(context)
        request.y_db.add(context)
        return redirect_back_to_context(request, context)
    return {
        'form': form,
        'back_url': request.GET.get('back', '')
    }


def delete(context, request):
    request.y_repo.trash.insert(context)
    request.session.flash(
        '{type} ({name}) was added to the trash'.format(
            type=context.type.title(),
            name=context.name,
        ), 'y.ok'
    )
    return redirect_back_to_parent(request, context)


def move(context, request):
    form = ContentMoveForm.from_request(request)
    if request.method == 'POST' and form.validate():
        request.y_repo.move(context).to(
            request.y_repo.query(Content).get(form.parent_id.data)
        )
        return redirect_back_to_context(request, context)
    return {'form_errors': form.errors}


# @TODO: not tested properly (integration test). Failed at fetching from repo.
def browse(request):
    def browse_url(*args, **kwargs):
        args = list(args)
        args.append('browse')

        if 'originator_id' in request.GET:
            kwargs['originator_id'] = request.GET['originator_id']
        if 'policy' in request.GET:
            kwargs['policy'] = request.GET['policy']

        return request.y_path(*args, **kwargs)

    policy = BrowsePolicy.get(
        request.GET['policy'],
        request.y_repo.query(Content).get(int(request.GET['originator_id']))
    )

    children = request.context.children().paginate(
        page_number(request.GET.get('page', 1)),
        per_page=10,
        error_out=False
    )

    return {
        'children': children,
        'browse_url': browse_url,
        'policy': policy,
    }


def login(request):
    """Logs a user in and sets the csrf token in the session

    Will redirect to GET parameter `back` if specified on successful login.

    :param request: Pyramid.request.Request
    :return: HTTPFound redirect or `LoginForm` if log in failed
    """
    form = LoginForm(request.POST)
    if request.method == 'POST' and form.validate():
        logged_in = request.y_user.login(
            form.email.data, form.password.data
        )
        if logged_in:
            request.session.new_csrf_token()
            return redirect_back(request, headers=logged_in)
        else:
            request.session.flash(
                'Could not log in: invalid email or password', 'y.errors'
            )
            return {'form': form}
    return {'form': form}


def logout(request):
    """Logs the current user out and clears the session

    Will redirect to GET parameter `back` if specified.

    :param request: Pyramid.request.Request
    :return: HTTPFound redirect
    """
    request.session.invalidate()
    logged_out = request.y_user.logout()

    return redirect_back(request, headers=logged_out)


def wrap_view(*view_callables_to_wrap):
    """ Decorator that will wrap a view callable with other view callables and
    merge the return values. This comes in handy as it allows you to compose
    a view from many smaller views.

    A simplified example::

        def view1(context, request):
            return {'view1': 1}

        def view2(context, request):
            return {'view1': 1}

        @wrap_view(view1, view2)
        def view3(context, request):
            return {'view3': 2}

        The return value of view3 when called will be the result of merging all
        the view's return value::

            {'view1': 1, 'view2': 2, 'view3': 3}

        This is equivalent of doing the following::

            rv = view1(context, request)
            rv.update(view2(context, request))
            rv.update(view3(context, request))

    This decorator assumes the return value of a view callable will be a dict.
    You can therefor only use it with view callable that returns a dict.

    The view callables will be given the same arguments as the decorated view.
    This means either a request or a context and a request.

    :param view_callables_to_wrap: One or more view callable to call before
     calling the decorated function.
    """
    def actual_decorator(decorated_function):
        decorated_function.__yoshimi_should_wrap_view__ = False

        @wraps(decorated_function)
        def _inner(*args, **kwargs):
            if decorated_function.__yoshimi_should_wrap_view__:
                rv = {}
                for view in view_callables_to_wrap:
                    rv.update(view(*args, **kwargs))
                rv.update(decorated_function(*args, **kwargs))
                return rv
            else:
                return decorated_function(*args, **kwargs)

        def venusian_callback(scanner, name, ob):
            decorated_function.__yoshimi_should_wrap_view__ = True

        venusian.attach(_inner, venusian_callback)

        return _inner

    return actual_decorator
