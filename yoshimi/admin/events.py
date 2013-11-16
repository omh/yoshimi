from pyramid.events import NewRequest
from pyramid.events import subscriber
from yoshimi.admin.fanstatic import js, css

@subscriber(NewRequest)
def new_request(event):
    js.need()
    css.need()
