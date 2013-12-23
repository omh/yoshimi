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

.. autoclass:: yoshimi.services.Trash
  :members:



URL generation
--------------

.. autofunction:: yoshimi.url.path
.. autofunction:: yoshimi.url.url
.. autofunction:: yoshimi.url.context_redirect_back
.. autofunction:: yoshimi.url.redirect_back
.. autofunction:: yoshimi.url.safe_redirect
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
