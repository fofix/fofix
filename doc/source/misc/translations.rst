Translations
============


Structure
---------

Here is the structure of translation directories::

    data
    │
    ├── po
    │   ├── messages.pot
    │   ├── <lang>.po
    │   ├── <lang>.po
    │   └── …
    │
    └── translations
        ├── <lang>.mo
        ├── <lang>.mo
        └── …

- ``data/po/messages.pot``: template for PO files
- ``data/po/<lang>.po``: PO file which contains strings with their translations
- ``data/translations/<lang>.mo``: generated MO file from its associated PO file


Manage the POT file
-------------------

To create a new POT file:

    .. code-block:: bash

        find . -type f -name "*.py" | xgettext --sort-output -o data/po/messages.pot -kN_ -k_ -f -

To update an existing POT file:

    .. code-block:: bash

        find . -type f -name "*.py" | xgettext -j --sort-output -o data/po/messages.pot -kN_ -k_ -f -


Add a language
--------------

To add a language you would like, you have several options.

1. Open an issue to request it: https://github.com/fofix/fofix/issues/new.
2. Ask for a new language on Transifex.
3. Make a pull request with the new PO file:

    .. code-block:: bash

        msginit --input=data/po/messages.pot --locale=<code> --output=data/po/<lang>.po


Translate
---------

To translate some strings, you should use our `Transifex project <https://www.transifex.com/fofix/fofix/>`_. Please, feel free to join us :).


.. note::

    Since there are a lot of strings to translate, it is easier using a web
    editor than using a local one like Poedit.

.. note::

    Transifex is not the best choice for translations because it's not open
    source anymore, but:

        - the community is still big
        - the interface looks nice.

    Other open source web editors could be used later, if Transifex is not great
    enough for us:

        - `Launchpad <https://translations.launchpad.net>`_
        - `Zanata <https://translate.zanata.org/project/view/fofix?dswid=9957>`_ (a project exists already, but is not used)
        - a self-hosted tool (Weblate, Pootle, …).
