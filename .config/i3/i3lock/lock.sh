#!/bin/sh

FOREGROUND='#BCC4C9'
FRAME_COLOR='#506A68'
HIGHLIGHT='#506A68'
WRONG_COLOR='#D95C5C'
BLANK='#00000000'
CLEAR="${FRAME_COLOR}22"
DEFAULT=$FRAME_COLOR
TEXT=$FOREGROUND
WRONG=$WRONG_COLOR
VERIFYING=$HIGHLIGHT

i3lock \
--insidever-color=$CLEAR       \
--ringver-color=$VERIFYING     \
\
--insidewrong-color=$CLEAR     \
--ringwrong-color=$WRONG       \
\
--inside-color=$BLANK          \
--ring-color=$DEFAULT          \
--line-color=$BLANK            \
--separator-color=$DEFAULT     \
\
--verif-color=$TEXT            \
--wrong-color=$TEXT            \
--time-color=$TEXT             \
--date-color=$TEXT             \
--layout-color=$TEXT           \
--keyhl-color=$WRONG           \
--bshl-color=$WRONG            \
\
--screen 1                     \
--blur 8                       \
--clock                        \
--indicator                    \
--time-str="%H:%M:%S"          \
--date-str="%A, %Y-%m-%d"      \
--keylayout 1
