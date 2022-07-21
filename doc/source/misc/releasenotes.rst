Release notes
=============

4.0.0 (unreleased)
------------------

Stages:

- alpha1: 2010-11-27
- alpha2: 2011-09-30

Notes:

- Will break compatibility with FoFiX v3

- Themes:

  - added possibility to customize hitflames (location, rotation, whether or not black is auto removed from the images)
  - added possibility to customize the POV
  - added possibility to customize the fps display location
  - added possibility to customize the pause menu text style
  - added support for a neck which shows when the multiplier reaches "4x"
  - added support for solo sidebars
  - added theme settings for control over how the color of tails and flames behave with sp/od
  - implemented a separate hitflames animation image for when starpower/overdrive is active
  - made all notes be able to be animated
  - made almost all images optional (see the *Uberlight* theme)
  - moved tons of images to folders
  - removed ``editor.png`` from themes as its no longer of any use
  - renamed ``backgrounds`` folder to ``stages``
  - render the main menu to plain text by default if ``main_text.png`` is not detected
  - rockmeter: added a new layer grouping system
  - rockmeter: added a new layer: circle layer (very handy for star fillup)
  - rockmeter: added new effects: scale, fade, animate
  - rockmeter: fixed some sliding effect issues
  - rockmeter: improved speed

  - *MLv4*: new theme
  - *ML GH3*: recreated the rockmeter with ``rockmeter.ini``
  - *Uberlight*: cleaned up to be the absolute minimum allowed by the engin.

- Game:

  - cleaned up the code to simplify it
  - made the solo neck scroll in to the very end of the neck instead of stopping at the frets
  - simplified hitflames: any supported hitflame image can now be rendered at the same time

- Other:

  - changed default frame limit to 60 FPS
  - fixed a rotation bug in image rendering
  - fixed menu text, optionsPanel, and BRE/Solo frame scaling issues
  - implemented song specific loading screen images
  - shared more code between the guitar and drums
  - added ``CMGL`` as a faster OpenGL binding
  - replace the PitchAnalyzer module with the ``pypitch`` one
  - rename the option *uploadurl_w67_starpower* to *uploadurl* in ``fofix.ini``
  - dependencies: bump `Pillow` to 6.2.2
  - added ``videoplayer`` as a reader for OGG video files (OGV)


3.122 (2019-11-28)
------------------

- Fix PIL imports (to use Pillow)
- Fix OGG imports
- Add the `Version.versionNum` function.


3.121 (2009-12-06)
------------------

Python version: > 2.6

- Increased performance
- A more precise and helpful error logging system
- Planning to cut support for Python 2.4 soon


3.120 (2009-09-22)
------------------

Stages:

- beta1: 2009-04-19
- beta2: 2009-06-28
- rc1: 2009-08-27

Over 170 issues were resolved by this latest version!

- Customizable AI difficulty
- Changed the hit window setting: in the "Mods, Cheats, and AI" section of the Settings menu, check your "Note Hit Window". Most players will want "Normal"
- Simplified 3D rendering
- Added 3 and 4-player modes
- Added detailed options menu text
- Added "Vocals" difficulty
- Added Jurgen vocals
- Added player profiles
- Added controller profiles
- Added support for GH:WT xbox360 guitar solo frets
- Added more themeable settings
- Fixed Neck rendering
- Fixed RB Co-Op saving
- Fixed high scores
- Fixed translations
- Fixed setlist sorting
- Fixed issues related to Animated Hitflames
- Fixed issues related to Big Rock Endings
- Fixed issues related to Cache
- Fixed issues related to Drums
- Fixed issues related to Pratice Mode
- Fixed issues related to Rendering
- Fixed issues appearing when pausing then unpausing the game
- Fixed Scoring issues: note hits, note streaks and accuracy
- Fixed various game crash or freeze (BRE, neck selection, overdrive, etc.)
- Fixed face-off battle note streaks
- Fixed MacOS X paths for configuration files and logs
- Added experimental shaders support: requires a videocard implementing OpenGL >= 2.0 and pyopengl 3.x
- PyOpenGL 2.0.1.x does not support shaders. Shaders support was introduced in 2.0.2.x. Thus, to get shaders under GNU/Linux, you'll have to use the python2.5 build


3.100 (2009-02-21)
------------------

Stages:

- beta1: 2009-01-12
- beta2: 2009-01-18
- beta3: 2009-01-25
- beta4: 2009-02-07
- rc1: 2009-02-08

Notes:

- Guitar picks will now repeat for menu and songlist scrolling
- Lyrics will no longer show during the song countdown
- No more double-and-triple song loading cycles
- Very basic Big Rock Ending support
- Drum Fills
- MIDI instrument input support
- Whammy pitch-bending support
- Basic 3D note.dae texturing support
- Songlist metadeta caching
- New tutorial song : a drum roll practice tutorial created by venom426.


3.030 (2008-11-19)
------------------

Stages:

- beta2: 2008-11-14
- beta1: 2008-11-07

Notes:

- Fixed issue 165
- The View thread timing: should result in major smoothness and stability improvements as well as mostly fixing[?] the double-loading screen issue)
- Removed the pyAmanith dependency
- Lighter the full package


3.025 (2008-10-30)
------------------


3.021 (2008-10-25)
------------------

Songlist Optimization


3.020 (2008-10-24)
------------------

- Fixed game freeze / hang caused by "Accuracy Words Pos" = "Center"
- Used rubjonny's FoF icon instead of the old style icon
- Fixed issue: where the song time countdown, once it reaches zero, starts counting back from 60 while the music track finishes (if it finishes after the midi, as a lot of songs do)
- Fixed issue: strumming a HOPO before pulling off to another doesn't work correctly
- Added evilynux's Timer.py patch that greatly reduces CPU usage in menus and in game
- Added basic score uploading feedback - the game will now tell you if the upload succeeded or failed
- Added logic to display resulting rank for your uploaded top score in the world chart: http://i36.tinypic.com/2cxzqyv.jpg
- Fixed HOPO markings on notes extremely close together, examples are found all over the Hell Freezes Over version of Hotel California
- Replaced all GuitarScene realtime string concatenation (slow) with % formatting (fast) -- only during gameplay (initialization concatenation is still present)
- Rewrote both Guitar and Drum starpower marking logic to occur only at initialization, not every time through the renderNotes() functions
- Rewrote starpower marking logic to only mark the actual last note as the starpower "final" instead of the entire last chord (this fixes the double drum starpower rewards)
- Prevented HOPO debug text from being rendered for drum players
  - Added optional support for theme-based failsound.ogg from worldrave's GH3 back and failed sounds
  - Added optional support for random choice between theme-based back1.ogg and back2.ogg instead of just out.ogg
- Wrote logic to stagger-mix crowd cheering sound files in a loop to create an endless cheering effect for the GameResults screen (a la GH2) if crowdcheers.ogg exists in the current theme
  - New setting under "Audio Options" -> "Results Cheer Loop" (default On) - will mix and endless loop of cheers during game results scoring
  - New setting under "Audio Options" -> "Cheer Loop Delay" (default 550) - this is the adjustable delay between mixing of a fresh crowd cheer into the loop (careful!)
- Ensured that if crowdcheers.ogg is not found, that starpower.ogg is not mixed twice whenever activating starpower
- Added slashy666's updated pause.png and editor.png to Rock Band 1 theme
- Added logic to catch a crash/hang when the game attempts to improperly delete a texture


3.017 (2008-10-17)
------------------

Fail Detection Fix

- Rewrote fail detection logic in GuitarScene.run() function to not be hardcoded for 2 players, to be compatible with future expansion


3.016 (2008-10-16)
------------------

Stages:

- alpha: 2008-10-16

Notes: Logging & Debugging Enhancements

- Enhanced "error" logfile entries to produce a helpful trace output like that created when running from sources and using an immediate / debug window (no code shown, just classes / functions / line numbers)
- fretsonfire.log file will now be created in the game folder you are running from (will appear in the same place fretsonfire.ini is created)
- Recompiled library.zip and FretsOnFire.exe from sources
- Updated GameEngine.versionstring to the correct value


3.015 (2008-10-15)
------------------

- Fixed pause layering during song countdown
- Ensured the accuracy indicator from the last note hit is not still displayed after a restart
- Ensured that just letting an entire guitar solo go by without attempting to hit any notes does not result in a 100% perfect solo
- Moved spinning star rotation angle calculation / update from Guitar render() function to run() function
- Added logic to catch when a drum chord (which counts individual notes for streak) skips a "note streak" threshold (like, from 99 to 101) and display the appropriate streak notification
- Added logic to flash the overdrive strings just before You Rock for Rock Band based themes
