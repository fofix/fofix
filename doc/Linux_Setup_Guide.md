##Debian/Ubuntu Installation Guide

>Note: Each Step stands on its own.
>If an intruction repeats, skip to the next instruction.
>For example, opening Terminal once is enough,
>you will not have to repeat it, if you move between steps without a break.

###Step 1: Download Source Code
1. Go to: https://github.com/fofix/fofix
2. Find the Green *Code* button. (On the top right of the page, to the left of About)
3. Click on this green button
4. Click on "Download ZIP" from the dropdown menu
5. Right click on the downloaded file (fofix-master.zip) and Select *Extract to*
6. Choose your *Documents* folder (you can choose any, this guide uses Documents folder)
7. Remember which folder you extracted to, we will need it soon enough.


####Step 2: Install Python
1. Open *Terminal*
2. Enter: `sudo apt install python2`
3. When prompted Enter: [Your Password]
4. When prompted Enter: "Y"

####Step 3: Install C++ Compiler
1. Open *Terminal*
2. Enter: `sudo apt install build-essential`

####Step 4: Install OpenGL
1. Open *Terminal*
2. Enter: `sudo apt-get update`
3. When prompted Enter: [Your Admin Password]
4. Enter: `sudo apt-get install libglu1-mesa-dev freeglut3-dev mesa-common-dev`
5. When prompted Enter: "Y"

####Step 5: Install ffmpeg
1. Open *Terminal*
2. Enter: `sudo apt-get update`
3. When prompted Enter: [Your Admin Password]
4. Enter: `sudo apt install ffmpeg`

####Step 6: Install pkg-config
1. Open *Terminal*
2. Enter: `sudo apt-get install pkg-config`
3. When prompted Enter: [Your Admin Password]

####Step 7: Install Unix Dependencies
1. Open *Terminal*
2. Enter: `sudo apt-get install libogg-dev libportmidi-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsoundtouch-dev libswscale-dev libtheora-dev libvorbis-dev mesa-utils portaudio19-dev`
3. When prompted Enter: [Your Admin Password]

####Step 8: Install Python Development Headers
1. Open *Terminal*
2. Enter: `sudo apt-get install python-dev`
3. When prompted Enter: [Your Admin Password]
4. When prompted Enter: "Y"

####Step 9: Install Pip2
1. Open *Terminal*
2. Enter:
    `sudo add-apt-repository universe`
    `sudo apt update`
    `sudo apt install python2`
    `curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py`
    `sudo python2 get-pip.py`
3. When prompted Enter: [Your Admin Password]

####Step 10: Install numpy, cynthon, python-opengl, gettext
1. Open *Terminal*
2. Enter: `sudo apt-get install python-dev`
3. When prompted Enter: [Your Admin Password]
4. Enter: `sudo pip2 install - numpy`
5. Enter: `sudo pip2 install --upgrade cython`
6. Enter: `sudo pip2 install PyOpenGL PyOpenGL_accelerate`
7. Enter: `sudo apt-get install gettext`

####Step 11: Build Native Modules
1. Open *Terminal*
2. Enter: `cd ~/Documents/fofix-master`
    - Replace Documents in 2. with the name of the folder you exacted fofix-master into.
3. Enter: `python setup.py build_ext --inplace --force`

####Step 12: Generate Translations
1. Open *Terminal*
2. Enter: `cd ~/Documents/fofix-master`
3. Enter: `python setup.py msgfmt`

####Step 13: Install Requirements
1. Open *Terminal*
2. Enter: `cd ~/Documents/fofix-master`
3. Enter: `pip install -r requirements.txt`

####Step 14: Run FOFIX
1. Open *Terminal*
2. Enter: `cd ~/Documents/fofix-master`
3. Enter: `python FoFiX.py`
