import sqlalchemy as sa
from yoshimi.content import ContentType, Content


class Article(ContentType, Content):
    title = sa.Column(sa.String(250))


class Folder(ContentType, Content):
    pass


def get_content(*args, **kwargs):
    """Returns a location with all required fields filled in"""
    c = Content(*args, **kwargs)
    if 'name' not in kwargs:
        c.name = "This is test content"
    if 'slug' not in kwargs:
        c.slug = "this-is-a-slug"

    return c


def get_article(*args, **kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = 'test folder'
    if 'slug' not in kwargs:
        kwargs['slug'] = 'test-article'

    return Article(*args, **kwargs)


def get_folder(*args, **kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = 'test folder'
    if 'slug' not in kwargs:
        kwargs['slug'] = 'test-folder'
    return Folder(*args, **kwargs)
