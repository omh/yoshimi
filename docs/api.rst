.. _api:

API
===


Content Types
-------------

.. autoclass:: yoshimi.content.Content
  :members:

.. autoclass:: yoshimi.content.ContentType
  :members:


Content Repository (repo)
-------------------------

.. autoclass:: yoshimi.repo.Repo
  :members:

.. autoclass:: yoshimi.repo.Query
  :members:


Trash
-----

.. autoclass:: yoshimi.trash.Trash
  :members:



URL generation
--------------

.. autofunction:: yoshimi.url.path
.. autofunction:: yoshimi.url.url
.. autofunction:: yoshimi.url.redirect_back_to_context
.. autofunction:: yoshimi.url.back_to_context_url
.. autofunction:: yoshimi.url.redirect_back_to_parent
.. autofunction:: yoshimi.url.safe_redirect_url
.. autoclass:: yoshimi.url.ResourceUrlAdapter
  :members:
.. autoclass:: yoshimi.url.RootFactory
  :members:


Templating
----------

.. autofunction:: yoshimi.templating.url_filter
.. autofunction:: yoshimi.templating.url_back_filter
.. autofunction:: yoshimi.templating.path_filter
.. autofunction:: yoshimi.templating.path_back_filter
