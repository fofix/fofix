#ifdef _WIN32
#include <windows.h>
#undef HAVE_HYPOT
#endif
#if !defined(__APPLE__)
#include <GL/gl.h>
#include <GL/glu.h>
#else
// OSX opengl headers
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#endif
