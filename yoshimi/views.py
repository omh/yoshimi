"""
    yoshimi.views
    ~~~~~~~~~

    This module provides all the views that make up Yoshimi.

    :copyright: (c) 2013 by Ole Morten Halvorsen
    :license: BSD, see LICENSE for more details.
"""
from yoshimi.browse import BrowsePolicy
from yoshimi.content import Location
from yoshimi.forms import LoginForm
from yoshimi.forms import ContentEditForm
from yoshimi.forms import ContentMoveForm
from yoshimi.url import path
from yoshimi.utils import LazyPagination
from yoshimi.utils import page_number
from yoshimi.utils import redirect_back


def index(request):
    children = LazyPagination(
        request.context.children(),
        page_number(request.GET.get('page', 1))
    )

    return {
        'children': children,
        'can_move': bool(request.context.parent)
    }


def edit(request):
    form = ContentEditForm.from_request(request)
    if request.method == 'POST' and form.validate():
        form.populate_obj(request.context.content)
        request.y_db.add(request.context.content)
        return redirect_back(request, path(request, request.context))
    return {
        'form': form,
        'back_url': request.GET.get('back', '')
    }


def move(request):
    form = ContentMoveForm.from_request(request)
    if request.method == 'POST' and form.validate():
        new_location = Location.query.get(form.parent_location_id.data)
        request.context.move(new_location)
        u = redirect_back(request, path(request, request.context))
        print("REDIR BACK %s" % u)
        return u
    return {'form_errors': form.errors}


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
        Location.query.get(int(request.GET['originator_id']))
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
