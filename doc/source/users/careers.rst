Make your own careers
=====================

FoFiX supports the career mode: unlock songs only if you success in previous ones!

Songs
-----

For each song you want to put in your career pack, in ``song.ini``:
    1. Add the key ``unlock_id``
    2. Put the id of the pack for its value (ex: ``unlock_id = gh3_1`` for the tier 1 of the GH3 pack)
    3. For encore songs of one tier, add the ``enc`` suffix to the id value (ex: ``gh3_1enc``)
    4. To order songs, add a number for your song to the id value (ex: ``gh3_1.1``)
    5. Add the key ``unlock_require`` with the id of the song you need to do as a value. If the song does not need to be unlocked, let the value empty
    6. Add the key ``unlock_text`` to display a text when the song is still locked.


Example::

    [song]
    ...
    unlock_id = gh3_2
    unlock_required = gh3_1
    unlock_text = Finish the 2nd tier of the GH3 pack!


Regroup song folders you want in your career pack in a folder (folder name ex: ``gh3``).


INI file
---------

Make a ``titles.ini`` file in your career pack folder. Here is an example of its content:

- section ``[titles]``:
    - key: ``sections``
    - value: each tear section names, spaced by a space
    - example: ``sections = tier1 tier2 bonus``
- sections ``[tearX]`` (one for each section defined before):
    - key: ``name``
    - value: the displayed name for the tier
    - example: ``name = 1. My first tear``

    * key: ``unlock_id``
    * value: the id of the tier (the same you put in ``song.ini``)
    * example: ``unlock_id = gh3_1``


Example::

    [titles]
    sections = tier1 tier2

    [tear1]
    name = 1. First tear
    unlock_id = gh3_1

    [tear2]
    name = 2. Second tear
    unlock_id = gh3_2
