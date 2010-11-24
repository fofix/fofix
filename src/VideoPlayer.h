/* Frets on Fire X (FoFiX)
 * Copyright (C) 2010 Team FoFiX
 *               2010 John Stumpo
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA  02110-1301, USA.
 */

#ifndef VIDEOPLAYER_H
#define VIDEOPLAYER_H

#include <glib.h>

typedef struct _VideoPlayer VideoPlayer;

VideoPlayer* video_player_new(const char* filename, GError** err);
void video_player_destroy(VideoPlayer* player);

GQuark video_player_error_quark(void);
#define VIDEO_PLAYER_ERROR video_player_error_quark()

typedef enum {
  VIDEO_PLAYER_NO_VIDEO,
  VIDEO_PLAYER_BAD_HEADERS
} VideoPlayerError;

#endif
