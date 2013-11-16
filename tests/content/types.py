from yoshimi.content import ContentType, Content


class Article(ContentType, Content):
    pass


class Folder(ContentType, Content):
    pass


def get_content(*args, **kwargs):
    """Returns a location with all required fields filled in"""
    c = Content(*args, **kwargs)
    c.name = "This is test content"
    c.slug = "this-is-a-slug"

    return c


def get_article(*args, **kwargs):
    if not 'name' in kwargs:
        kwargs['name'] = 'test folder'
    if not 'slug' in kwargs:
        kwargs['slug'] = 'test-article'

    return Article(*args, **kwargs)


def get_folder(*args, **kwargs):
    if not 'name' in kwargs:
        kwargs['name'] = 'test folder'
    if not 'slug' in kwargs:
        kwargs['slug'] = 'test-folder'
    return Folder(*args, **kwargs)
