Translations
============


To add translations:
    1. add your language if not present
    2. edit the translation file
    3. build the translation file
    4. submit your translation

Translation folder: ``data/translations``.


Requirements
------------

You will need to install ``gettext`` to compile translations.


Add your language
-----------------

To add your language "LANG", copy the file ``data/po/xx.po`` to ``data/po/LANG.po``.


Edit a translation file
------------------------

Edit your translation file ``data/po/LANG.po`` with any text editor, but `Poedit <https://poedit.net/>`_ is recommended. You have to edit ``msgstr`` lines.

Update the header too with your information if not done.


Build the translation file
--------------------------

Convert the file ``LANG.po`` to ``LANG.mo``. To do that, you can use:
    - ``Poedit``
    - ``gettext`` (via the ``msgfmt`` tool)

Put the generated file ``LANG.mo`` to ``data/translations/`` to check your
translation.


Submit your translation
-----------------------

Do a pull request with your translations.
