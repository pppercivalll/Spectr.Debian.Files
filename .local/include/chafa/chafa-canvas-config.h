/* -*- Mode: C; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */

/* Copyright (C) 2018-2025 Hans Petter Jansson
 *
 * This file is part of Chafa, a program that shows pictures on text terminals.
 *
 * Chafa is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Chafa is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Chafa.  If not, see <http://www.gnu.org/licenses/>. */

#ifndef __CHAFA_CANVAS_CONFIG_H__
#define __CHAFA_CANVAS_CONFIG_H__

#if !defined (__CHAFA_H_INSIDE__) && !defined (CHAFA_COMPILATION)
# error "Only <chafa.h> can be included directly."
#endif

#include <chafa-symbol-map.h>

G_BEGIN_DECLS

/* Canvas config */

typedef struct ChafaCanvasConfig ChafaCanvasConfig;

CHAFA_AVAILABLE_IN_ALL
ChafaCanvasConfig *chafa_canvas_config_new (void);
CHAFA_AVAILABLE_IN_ALL
ChafaCanvasConfig *chafa_canvas_config_copy (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_ref (ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_unref (ChafaCanvasConfig *config);

CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_get_geometry (const ChafaCanvasConfig *config, gint *width_out, gint *height_out);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_geometry (ChafaCanvasConfig *config, gint width, gint height);

CHAFA_AVAILABLE_IN_1_4
void chafa_canvas_config_get_cell_geometry (const ChafaCanvasConfig *config, gint *cell_width_out, gint *cell_height_out);
CHAFA_AVAILABLE_IN_1_4
void chafa_canvas_config_set_cell_geometry (ChafaCanvasConfig *config, gint cell_width, gint cell_height);

CHAFA_AVAILABLE_IN_ALL
ChafaCanvasMode chafa_canvas_config_get_canvas_mode (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_canvas_mode (ChafaCanvasConfig *config, ChafaCanvasMode mode);

CHAFA_AVAILABLE_IN_1_4
ChafaColorExtractor chafa_canvas_config_get_color_extractor (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_4
void chafa_canvas_config_set_color_extractor (ChafaCanvasConfig *config, ChafaColorExtractor color_extractor);

CHAFA_AVAILABLE_IN_ALL
ChafaColorSpace chafa_canvas_config_get_color_space (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_color_space (ChafaCanvasConfig *config, ChafaColorSpace color_space);

CHAFA_AVAILABLE_IN_ALL
const ChafaSymbolMap *chafa_canvas_config_peek_symbol_map (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_symbol_map (ChafaCanvasConfig *config, const ChafaSymbolMap *symbol_map);

CHAFA_AVAILABLE_IN_ALL
const ChafaSymbolMap *chafa_canvas_config_peek_fill_symbol_map (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_fill_symbol_map (ChafaCanvasConfig *config, const ChafaSymbolMap *fill_symbol_map);

CHAFA_AVAILABLE_IN_ALL
gfloat chafa_canvas_config_get_transparency_threshold (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_transparency_threshold (ChafaCanvasConfig *config, gfloat alpha_threshold);

CHAFA_AVAILABLE_IN_ALL
guint32 chafa_canvas_config_get_fg_color (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_fg_color (ChafaCanvasConfig *config, guint32 fg_color_packed_rgb);

CHAFA_AVAILABLE_IN_ALL
guint32 chafa_canvas_config_get_bg_color (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_bg_color (ChafaCanvasConfig *config, guint32 bg_color_packed_rgb);

CHAFA_AVAILABLE_IN_ALL
gfloat chafa_canvas_config_get_work_factor (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_work_factor (ChafaCanvasConfig *config, gfloat work_factor);

CHAFA_AVAILABLE_IN_ALL
gboolean chafa_canvas_config_get_preprocessing_enabled (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_ALL
void chafa_canvas_config_set_preprocessing_enabled (ChafaCanvasConfig *config, gboolean preprocessing_enabled);

CHAFA_AVAILABLE_IN_1_2
ChafaDitherMode chafa_canvas_config_get_dither_mode (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_2
void chafa_canvas_config_set_dither_mode (ChafaCanvasConfig *config, ChafaDitherMode dither_mode);

CHAFA_AVAILABLE_IN_1_2
void chafa_canvas_config_get_dither_grain_size (const ChafaCanvasConfig *config, gint *width_out, gint *height_out);
CHAFA_AVAILABLE_IN_1_2
void chafa_canvas_config_set_dither_grain_size (ChafaCanvasConfig *config, gint width, gint height);

CHAFA_AVAILABLE_IN_1_2
gfloat chafa_canvas_config_get_dither_intensity (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_2
void chafa_canvas_config_set_dither_intensity (ChafaCanvasConfig *config, gfloat intensity);

CHAFA_AVAILABLE_IN_1_4
ChafaPixelMode chafa_canvas_config_get_pixel_mode (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_4
void chafa_canvas_config_set_pixel_mode (ChafaCanvasConfig *config, ChafaPixelMode pixel_mode);

CHAFA_AVAILABLE_IN_1_6
ChafaOptimizations chafa_canvas_config_get_optimizations (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_6
void chafa_canvas_config_set_optimizations (ChafaCanvasConfig *config, ChafaOptimizations optimizations);

CHAFA_AVAILABLE_IN_1_8
gboolean chafa_canvas_config_get_fg_only_enabled (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_8
void chafa_canvas_config_set_fg_only_enabled (ChafaCanvasConfig *config, gboolean fg_only_enabled);

CHAFA_AVAILABLE_IN_1_14
ChafaPassthrough chafa_canvas_config_get_passthrough (const ChafaCanvasConfig *config);
CHAFA_AVAILABLE_IN_1_14
void chafa_canvas_config_set_passthrough (ChafaCanvasConfig *config, ChafaPassthrough passthrough);

G_END_DECLS

#endif /* __CHAFA_CANVAS_CONFIG_H__ */
