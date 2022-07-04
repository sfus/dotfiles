#!/bin/sh

if [ `which lesskey` ]; then
    lesskey -o ~/.lesskey lesskey.conf
fi
