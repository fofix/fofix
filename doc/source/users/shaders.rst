Shaders
=======

Definition
-----------

A shader is a small program, which affects every vertex and pixel of object. A shader is splitted in 2 parts:
    - vertex shader: this one can transform any surface, for example, it can make neck wavy
    - pixel (fragment) shader: it can change color of every pixel on the screen


How to create a shader
----------------------

- Folder: ``data/shaders/``
- Files:
    - ``myshader.vert``: vertex shader, C-like code
    - ``myshader.frag``: fragment shader, C-like code
