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

#ifdef _MSC_VER
#define _CRT_SECURE_NO_DEPRECATE
#endif

#include "VideoPlayer.h"

#include "glwrap.h"
#include <libswscale/swscale.h>
#include <ogg/ogg.h>
#include <theora/theoradec.h>

#include <errno.h>
#include <stdio.h>

struct _VideoPlayer {
  FILE* file;
  ogg_sync_state osync;
  GHashTable* stream_table;
  ogg_page current_page;
  gboolean have_video;
  ogg_stream_state* vstream;
  th_info tinfo;
  th_comment tcomment;
  th_setup_info* tsetup;
  gboolean eof;
  th_dec_ctx* vdecoder;
  gboolean playing;
  glong playback_position;  /* microseconds */
  GTimeVal playback_start_time;
  GLuint video_texture;
  ogg_int64_t decode_granpos;
  th_ycbcr_buffer frame_buffer;
  struct SwsContext* sws_context;
  int tex_width;
  int tex_height;
  guchar* tex_buffer;
  gboolean buffer_dirty;
};

static void destroy_stream(gpointer data)
{
  ogg_stream_clear(data);
  g_free(data);
}

static gboolean demux_next_page(VideoPlayer* player, GError** err)
{
  int serialno;
  ogg_stream_state* ostream;

  /* Demux the next page into player->current_page. */
  while (ogg_sync_pageout(&player->osync, &player->current_page) != 1) {
    char* buf = ogg_sync_buffer(&player->osync, 65536);
    int bytes = fread(buf, 1, 65536, player->file);
    if (bytes == 0) {
      player->eof = TRUE;
      return TRUE;
    } else if (bytes < 0) {
      g_set_error(err, G_FILE_ERROR, g_file_error_from_errno(errno),
        "Failed to read video: %s", g_strerror(errno));
      return FALSE;
    }
    ogg_sync_wrote(&player->osync, bytes);
  }

  /* Dispatch it to the correct ogg_stream_state. */
  serialno = ogg_page_serialno(&player->current_page);
  ostream = g_hash_table_lookup(player->stream_table, &serialno);
  if (ostream != NULL) {
    ogg_stream_pagein(ostream, &player->current_page);
  } else if (ogg_page_bos(&player->current_page)) {
    int* key = g_new(int, 1);
    *key = serialno;
    ostream = g_new(ogg_stream_state, 1);
    ogg_stream_init(ostream, serialno);
    g_hash_table_insert(player->stream_table, key, ostream);
    ogg_stream_pagein(ostream, &player->current_page);
  }
  return TRUE;
}

static guint32 next_power_of_two(guint32 n)
{
  n--;
  n |= n >> 1;
  n |= n >> 2;
  n |= n >> 4;
  n |= n >> 8;
  n |= n >> 16;
  n++;
  return n;
}

static void update_texture(VideoPlayer* player)
{
  /* TODO: handle pic_[xy] correctly so the whole Theora testsuite works */
  const uint8_t* const src[] = {player->frame_buffer[0].data, player->frame_buffer[1].data, player->frame_buffer[2].data};
  int src_stride[] = {player->frame_buffer[0].stride, player->frame_buffer[1].stride, player->frame_buffer[2].stride};
  uint8_t* dest[] = {player->tex_buffer};
  int dest_stride[] = {player->tex_width * 4};
  sws_scale(player->sws_context, src, src_stride, 0, player->tinfo.pic_height, dest, dest_stride);
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, player->tex_width, player->tex_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, player->tex_buffer);
  player->buffer_dirty = FALSE;
}

static gboolean demux_headers(VideoPlayer* player, GError** err)
{
  /* Go through the stream header pages, looking for one that starts a Theora stream. */
  while (demux_next_page(player, err)) {
    /* If the page isn't a header, we're done this step. */
    if (player->eof || !ogg_page_bos(&player->current_page))
      goto got_all_headers;

    if (!player->have_video) {
      /* Grab the first packet and check it for Theoraness.
         Otherwise forget about the stream. */
      int header_status;
      ogg_packet pkt;

      int serialno = ogg_page_serialno(&player->current_page);
      ogg_stream_state* ostream = g_hash_table_lookup(player->stream_table, &serialno);
      if (ogg_stream_packetout(ostream, &pkt) != 1) {
        g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_HEADERS,
          "Bad headers in video file.");
        return FALSE;
      }

      header_status = th_decode_headerin(&player->tinfo, &player->tcomment, &player->tsetup, &pkt);
      if (header_status == TH_ENOTFORMAT) {
        /* Forget the stream - it's not Theora. */
        g_hash_table_remove(player->stream_table, &serialno);
      } else if (header_status < 0) {
        g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_HEADERS,
          "Bad headers in Theora stream.");
        return FALSE;
      } else {
        player->have_video = TRUE;
        player->vstream = ostream;
        /* And keep looping through the header pages so we can throw out the other streams. */
      }
    } else {
      /* Throw it out - we already found the stream. */
      int serialno = ogg_page_serialno(&player->current_page);
      g_hash_table_remove(player->stream_table, &serialno);
    }
  }
  /* If we got here, demux_next_page exploded before we even finished the stream headers. */
  return FALSE;

got_all_headers:
  if (!player->have_video) {
    g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_NO_VIDEO,
      "Failed to find a Theora stream in the video file.");
    return FALSE;
  }

  /* Get the rest of the headers. */
  while (!player->eof) {
    ogg_packet pkt;
    while (ogg_stream_packetout(player->vstream, &pkt) == 1) {
      int header_status = th_decode_headerin(&player->tinfo, &player->tcomment, &player->tsetup, &pkt);
      if (header_status < 0) {
        g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_HEADERS,
          "Bad headers in Theora stream.");
        return FALSE;
      } else if (header_status == 0) {
        /* We have everything we need to start decoding, and we have the first video packet. */
        int decode_status;
        int pix_format;
        player->vdecoder = th_decode_alloc(&player->tinfo, player->tsetup);
        player->playing = FALSE;
        player->playback_position = 0;
        decode_status = th_decode_packetin(player->vdecoder, &pkt, &player->decode_granpos);
        if (decode_status != 0) {
          g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_DATA,
            "An error occurred decoding a Theora packet.");
          return FALSE;
        }
        th_decode_ycbcr_out(player->vdecoder, player->frame_buffer);

        player->tex_width = next_power_of_two(player->tinfo.pic_width);
        player->tex_height = next_power_of_two(player->tinfo.pic_height);
        player->tex_buffer = g_malloc(player->tex_width * player->tex_height * 4);
        switch (player->tinfo.pixel_fmt) {
          case TH_PF_420:
            pix_format = AV_PIX_FMT_YUV420P;
            break;
          case TH_PF_422:
            pix_format = AV_PIX_FMT_YUV422P;
            break;
          case TH_PF_444:
            pix_format = AV_PIX_FMT_YUV444P;
            break;
          default:
            g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_HEADERS,
              "Bad pixel format in Theora stream.");
            return FALSE;
        }
        player->sws_context = sws_getContext(player->tinfo.pic_width, player->tinfo.pic_height, pix_format, player->tex_width, player->tex_height, AV_PIX_FMT_RGBA, SWS_FAST_BILINEAR, NULL, NULL, NULL);

        glBindTexture(GL_TEXTURE_2D, player->video_texture);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        update_texture(player);
        return TRUE;
      }
      /* Otherwise, there are still more header packets needed. */
    }
    if (!demux_next_page(player, err))
      return FALSE;
  }

  g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_HEADERS,
    "Failed to find all necessary Theora headers.");
  return FALSE;
}

VideoPlayer* video_player_new(const char* filename, GError** err)
{
  VideoPlayer* player = g_new0(VideoPlayer, 1);

  player->file = fopen(filename, "rb");
  if (player->file == NULL) {
    g_set_error(err, G_FILE_ERROR, g_file_error_from_errno(errno),
      "Failed to open video: %s", g_strerror(errno));
    g_free(player);
    return NULL;
  }

  player->stream_table = g_hash_table_new_full(g_int_hash, g_int_equal, g_free, destroy_stream);
  ogg_sync_init(&player->osync);
  th_info_init(&player->tinfo);
  th_comment_init(&player->tcomment);
  glGenTextures(1, &player->video_texture);
  if (!demux_headers(player, err)) {
    video_player_destroy(player);
    return NULL;
  }
  return player;
}

void video_player_destroy(VideoPlayer* player)
{
  if (player->vdecoder != NULL)
    th_decode_free(player->vdecoder);
  if (player->tsetup != NULL)
    th_setup_free(player->tsetup);
  if (player->sws_context != NULL)
    sws_freeContext(player->sws_context);
  if (player->tex_buffer != NULL)
    g_free(player->tex_buffer);
  glDeleteTextures(1, &player->video_texture);
  th_comment_clear(&player->tcomment);
  th_info_clear(&player->tinfo);
  g_hash_table_destroy(player->stream_table);
  ogg_sync_clear(&player->osync);
  fclose(player->file);
  g_free(player);
}

void video_player_play(VideoPlayer* player)
{
  g_get_current_time(&player->playback_start_time);
  g_time_val_add(&player->playback_start_time, -player->playback_position);
  player->playing = TRUE;
}

void video_player_pause(VideoPlayer* player)
{
  player->playing = FALSE;
}

gboolean video_player_bind_frame(VideoPlayer* player, GError** err)
{
  glBindTexture(GL_TEXTURE_2D, player->video_texture);

  /* Advance the playback position if we're playing. */
  if (player->playing) {
    GTimeVal now;
    g_get_current_time(&now);
    if (!video_player_advance(player, (now.tv_sec - player->playback_start_time.tv_sec) + 1e-6 * (now.tv_usec - player->playback_start_time.tv_usec), err))
      return FALSE;
  }

  if (player->buffer_dirty)
    update_texture(player);

  return TRUE;
}

gboolean video_player_advance(VideoPlayer* player, double newpos, GError** err)
{
  player->playback_position = (glong)(1000000 * newpos);

  while (th_granule_time(player->vdecoder, player->decode_granpos) * 1000000 < player->playback_position) {
    ogg_packet pkt;
    int decode_status;

    /* Get the next packet. */
    if (ogg_stream_packetout(player->vstream, &pkt) != 1) {
      if (player->eof) {
        video_player_pause(player);
        break;
      }
      if (!demux_next_page(player, err))
        return FALSE;
      continue;
    }

    decode_status = th_decode_packetin(player->vdecoder, &pkt, &player->decode_granpos);
    if (decode_status != 0 && decode_status != TH_DUPFRAME) {
      g_set_error(err, VIDEO_PLAYER_ERROR, VIDEO_PLAYER_BAD_DATA,
        "An error occurred decoding a Theora packet.");
      return FALSE;
    }

    if (decode_status == 0) {
      th_decode_ycbcr_out(player->vdecoder, player->frame_buffer);
      player->buffer_dirty = TRUE;
    }
  }

  return TRUE;
}

gboolean video_player_eof(const VideoPlayer* player)
{
  return player->eof;
}

double video_player_aspect_ratio(const VideoPlayer* player)
{
  return player->tinfo.pic_width / (double)player->tinfo.pic_height;
}

GQuark video_player_error_quark(void)
{
  return g_quark_from_static_string("video-player-error-quark");
}
