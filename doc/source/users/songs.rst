Songs
=====

Songs folder: `data/songs/`.


Song files
-----------

A song is a folder which contains multiple files:
    * song.ini (config)
    * song.ogg
    * script.txt (lyrics)

    - notes.mid
    - acoustic.ogg
    - bass.ogg
    - crowd.ogg
    - drums.ogg
    - guitar.ogg
    - piano.ogg
    - rhythm.ogg
    - vocals.ogg

    * preview.ogg
    * video.ogg (background video)

    - label.png


Create a song
-------------

Tools
+++++

Some tools will help you creating a song for FoFiX:

- `EOF <http://www.t3-i.com/pages/project.php?id=eof>`_ - `unofficial guide <http://www.fretsonfire.net/forums/viewtopic.php?t=1938>`_


INI file
+++++++++

The file ``song.ini`` is the configuration file for the song. Here is its
contents.

- Header section: ``[song]``
- Format: ``key = value``


+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| Key                    | Value type | FoFiX | Description                                                                         |
+========================+============+=======+=====================================================================================+
| ``album``              | str        |   ✓   | Album name                                                                          |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``artist``             | str        |   ✓   | Artist who made the song                                                            |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``background``         | str        |       | (Performous) Filename of image to display in the background during gameplay         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``cassettecolor``      | hexcolors  |   ✓   | Color of the cassette tape                                                          |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``count``              | int        |   ✓   | How many times played                                                               |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``cover``              | str        |       | (Performous) Filename of cover image                                                |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``delay``              | int        |   ✓   | Delays the notes, negative values works as well (in milliseconds)                   |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``diff_band``          | Value      |   ✓   | Set the difficulty for band                                                         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``diff_bass``          | Value      |   ✓   | Set the difficulty for bass                                                         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``diff_drums``         | Value      |   ✓   | Set the difficulty for drums                                                        |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``diff_guitar``        | Value      |   ✓   | Set the difficulty for guitar                                                       |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``frets``              | str        |   ✓   | Name of the maker / converter of the song                                           |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``genre``              | str        |   ✓   | Genre of music                                                                      |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``hopofreq``           | Value      |   ✓   | HOPO Frequency setting, requires the user setting "Song HOPO Freq" be set to "Auto" |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``icon``               | Value      |   ✓   | Sets icon to use for song title                                                     |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``loading_phrase``     | str        |   ✓   | Text that is displayed when song is loading                                         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``name``               | str        |   ✓   | Song title                                                                          |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``preview_start_time`` | int        |       | (Performous) Preview start time (in milliseconds)                                   |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``scores``             | str        |   ✓   | Generated: encoded highscores                                                       |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``scores_ext``         | str        |   ✓   | Generated: encoded score info                                                       |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``tags``               | Value      |   ✓   | Indicates a cover version so that "As Made famous by [artist]" is displayed         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``tutorial``           | boolean    |   ✓   | Hide the song in quickplay if it is the tutorial song                               |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``unlock_id``          | Tier       |   ✓   | Career mode: indicates the tier it belongs to                                       |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``unlock_require``     | Tier       |   ✓   | Career mode: indicates the tier needed to be finished for the song to be unlocked   |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``unlock_text``        | str        |   ✓   | Career mode: text that is displayed when the song is locked                         |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``version``            | int        |   ✓   | Version of the song                                                                 |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``video``              | str        |   ✓   | Video filename relative to song folder                                              |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``video_end_time``     | int        |   ✓   | Video end time (in milliseconds)                                                    |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``video_start_time``   | int        |   ✓   | Video start time (in milliseconds)                                                  |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+
| ``year``               | int        |   ✓   | Year in which the song has been published / made                                    |
+------------------------+------------+-------+-------------------------------------------------------------------------------------+




Value types:
    - boolean: 0 or 1
    - hexcolors: hexadecimal number
    - int: a number
    - str: text
    - Tier: the song id
    - Value:
        - ``icon`` values: rb1, rb2, rbdlc, rbtpk, gh1, gh2, gh2dlc, gh3, gh3dlc, gh80s, gha, ghm, ph1, ph2, ph3, ph4, phm
        - ``tag`` value: cover
        - ``diff_XXX`` values: 0 - 6
        - ``hopofreq`` values: 0 - 5
            - 0: "Least"
            - 1: "Less"
            - 2: "Normal"
            - 3: "More"
            - 4: "Even more"
            - 5: "Most"


Compatibility
-------------

Thanks to open source formats, FoFiX songs are compatible with many softwares like:
    - `PhaseShift <http://www.dwsk.co.uk/index_phase_shift.html>`_
    - `Performous <http://performous.org/>`_
