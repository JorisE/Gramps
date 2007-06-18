#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2005  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

import cStringIO

_onebyte = {
    '\x8D' : u'\x20\x0D', '\x8E' : u'\x20\x0C', '\xA1' : u'\x01\x41',
    '\xA2' : u'\xD8',     '\xA3' : u'\xD0',     '\xA4' : u'\xDE',
    '\xA5' : u'\xC6',     '\xA6' : u'\x01\x52', '\xA7' : u'\x02\xB9',
    '\xA8' : u'\xB7',     '\xA9' : u'\x26\x6D', '\xAA' : u'\xAE',
    '\xAB' : u'\xB1',     '\xAC' : u'\x01\xA0', '\xAD' : u'\x01\xAF',
    '\xAE' : u'\x02\xBE', '\xB0' : u'\x02\xBF', '\xB1' : u'\x01\x42',
    '\xB2' : u'\xF8',     '\xB3' : u'\x01\x11', '\xB4' : u'\xFE',
    '\xB5' : u'\xE6',     '\xB6' : u'\x01\x53', '\xB7' : u'\x02\xBA',
    '\xB8' : u'\x01\x31', '\xB9' : u'\xA3',     '\xBA' : u'\xF0',
    '\xBC' : u'\x01\xA1', '\xBD' : u'\x01\xB0', '\xC0' : u'\xB0',
    '\xC1' : u'\x21\x13', '\xC2' : u'\x21\x17', '\xC3' : u'\xA9',
    '\xC4' : u'\x26\x6F', '\xC5' : u'\xBF',     '\xC6' : u'\xA1',
    '\xCF' : u'\xDF',     '\xE0' : u'\x03\x09', '\xE1' : u'\x03',
    '\xE2' : u'\x03\x01', '\xE3' : u'\x03\x02', '\xE4' : u'\x03\x03',
    '\xE5' : u'\x03\x04', '\xE6' : u'\x03\x06', '\xE7' : u'\x03\x07',
    '\xE9' : u'\x03\x0C', '\xEA' : u'\x03\x0A', '\xEB' : u'\xFE\x20',
    '\xEC' : u'\xFE\x21', '\xED' : u'\x03\x15', '\xEE' : u'\x03\x0B',
    '\xEF' : u'\x03\x10', '\xF0' : u'\x03\x27', '\xF1' : u'\x03\x28',
    '\xF2' : u'\x03\x23', '\xF3' : u'\x03\x24', '\xF4' : u'\x03\x25',
    '\xF5' : u'\x03\x33', '\xF6' : u'\x03\x32', '\xF7' : u'\x03\x26',
    '\xF8' : u'\x03\x1C', '\xF9' : u'\x03\x2E', '\xFA' : u'\xFE\x22',
    '\xFB' : u'\xFE\x23', '\xFE' : u'\x03\x13',
    }

_twobyte = {
    '\xE0\x41' : u'\x1E\xA2', '\xE0\x45' : u'\x1E\xBA', '\xE0\x49' : u'\x1E\xC8',
    '\xE0\x4F' : u'\x1E\xCE', '\xE0\x55' : u'\x1E\xE6', '\xE0\x59' : u'\x1E\xF6',
    '\xE0\x61' : u'\x1E\xA3', '\xE0\x65' : u'\x1E\xBB', '\xE0\x69' : u'\x1E\xC9',
    '\xE0\x6F' : u'\x1E\xCF', '\xE0\x75' : u'\x1E\xE7', '\xE0\x79' : u'\x1E\xF7',
    '\xE1\x41' : u'\xC0',     '\xE1\x45' : u'\xC8',     '\xE1\x49' : u'\xCC',
    '\xE1\x4F' : u'\xD2',     '\xE1\x55' : u'\xD9',     '\xE1\x57' : u'\x1E\x80',
    '\xE1\x59' : u'\x1E\xF2', '\xE1\x61' : u'\xE0',     '\xE1\x65' : u'\xE8',
    '\xE1\x69' : u'\xEC',     '\xE1\x6F' : u'\xF2',     '\xE1\x75' : u'\xF9',
    '\xE1\x77' : u'\x1E\x81', '\xE1\x79' : u'\x1E\xF3', '\xE2\x41' : u'\xC1',
    '\xE2\x43' : u'\x01\x06', '\xE2\x45' : u'\xC9',     '\xE2\x47' : u'\x01\xF4',
    '\xE2\x49' : u'\xCD',     '\xE2\x4B' : u'\x1E\x30', '\xE2\x4C' : u'\x01\x39',
    '\xE2\x4D' : u'\x1E\x3E', '\xE2\x4E' : u'\x01\x43', '\xE2\x4F' : u'\xD3',
    '\xE2\x50' : u'\x1E\x54', '\xE2\x52' : u'\x01\x54', '\xE2\x53' : u'\x01\x5A',
    '\xE2\x55' : u'\xDA',     '\xE2\x57' : u'\x1E\x82', '\xE2\x59' : u'\xDD',
    '\xE2\x5A' : u'\x01\x79', '\xE2\x61' : u'\xE1',     '\xE2\x63' : u'\x01\x07',
    '\xE2\x65' : u'\xE9',     '\xE2\x67' : u'\x01\xF5', '\xE2\x69' : u'\xED',
    '\xE2\x6B' : u'\x1E\x31', '\xE2\x6C' : u'\x01\x3A', '\xE2\x6D' : u'\x1E\x3F',
    '\xE2\x6E' : u'\x01\x44', '\xE2\x6F' : u'\xF3',     '\xE2\x70' : u'\x1E\x55',
    '\xE2\x72' : u'\x01\x55', '\xE2\x73' : u'\x01\x5B', '\xE2\x75' : u'\xFA',
    '\xE2\x77' : u'\x1E\x83', '\xE2\x79' : u'\xFD',     '\xE2\x7A' : u'\x01\x7A',
    '\xE2\xA5' : u'\x01\xFC', '\xE2\xB5' : u'\x01\xFD', '\xE3\x41' : u'\xC2',
    '\xE3\x43' : u'\x01\x08', '\xE3\x45' : u'\xCA',     '\xE3\x47' : u'\x01\x1C',
    '\xE3\x48' : u'\x01\x24', '\xE3\x49' : u'\xCE',     '\xE3\x4A' : u'\x01\x34',
    '\xE3\x4F' : u'\xD4',     '\xE3\x53' : u'\x01\x5C', '\xE3\x55' : u'\xDB',
    '\xE3\x57' : u'\x01\x74', '\xE3\x59' : u'\x01\x76', '\xE3\x5A' : u'\x1E\x90',
    '\xE3\x61' : u'\xE2',     '\xE3\x63' : u'\x01\x09', '\xE3\x65' : u'\xEA',
    '\xE3\x67' : u'\x01\x1D', '\xE3\x68' : u'\x01\x25', '\xE3\x69' : u'\xEE',
    '\xE3\x6A' : u'\x01\x35', '\xE3\x6F' : u'\xF4',     '\xE3\x73' : u'\x01\x5D',
    '\xE3\x75' : u'\xFB',     '\xE3\x77' : u'\x01\x75', '\xE3\x79' : u'\x01\x77',
    '\xE3\x7A' : u'\x1E\x91', '\xE4\x41' : u'\xC3',     '\xE4\x45' : u'\x1E\xBC',
    '\xE4\x49' : u'\x01\x28', '\xE4\x4E' : u'\xD1',     '\xE4\x4F' : u'\xD5',
    '\xE4\x55' : u'\x01\x68', '\xE4\x56' : u'\x1E\x7C', '\xE4\x59' : u'\x1E\xF8',
    '\xE4\x61' : u'\xE3',     '\xE4\x65' : u'\x1E\xBD', '\xE4\x69' : u'\x01\x29',
    '\xE4\x6E' : u'\xF1',     '\xE4\x6F' : u'\xF5',     '\xE4\x75' : u'\x01\x69',
    '\xE4\x76' : u'\x1E\x7D', '\xE4\x79' : u'\x1E\xF9', '\xE5\x41' : u'\x01',
    '\xE5\x45' : u'\x01\x12', '\xE5\x47' : u'\x1E\x20', '\xE5\x49' : u'\x01\x2A',
    '\xE5\x4F' : u'\x01\x4C', '\xE5\x55' : u'\x01\x6A', '\xE5\x61' : u'\x01\x01',
    '\xE5\x65' : u'\x01\x13', '\xE5\x67' : u'\x1E\x21', '\xE5\x69' : u'\x01\x2B',
    '\xE5\x6F' : u'\x01\x4D', '\xE5\x75' : u'\x01\x6B', '\xE5\xA5' : u'\x01\xE2',
    '\xE5\xB5' : u'\x01\xE3', '\xE6\x41' : u'\x01\x02', '\xE6\x45' : u'\x01\x14',
    '\xE6\x47' : u'\x01\x1E', '\xE6\x49' : u'\x01\x2C', '\xE6\x4F' : u'\x01\x4E',
    '\xE6\x55' : u'\x01\x6C', '\xE6\x61' : u'\x01\x03', '\xE6\x65' : u'\x01\x15',
    '\xE6\x67' : u'\x01\x1F', '\xE6\x69' : u'\x01\x2D', '\xE6\x6F' : u'\x01\x4F',
    '\xE6\x75' : u'\x01\x6D', '\xE7\x42' : u'\x1E\x02', '\xE7\x43' : u'\x01\x0A',
    '\xE7\x44' : u'\x1E\x0A', '\xE7\x45' : u'\x01\x16', '\xE7\x46' : u'\x1E\x1E',
    '\xE7\x47' : u'\x01\x20', '\xE7\x48' : u'\x1E\x22', '\xE7\x49' : u'\x01\x30',
    '\xE7\x4D' : u'\x1E\x40', '\xE7\x4E' : u'\x1E\x44', '\xE7\x50' : u'\x1E\x56',
    '\xE7\x52' : u'\x1E\x58', '\xE7\x53' : u'\x1E\x60', '\xE7\x54' : u'\x1E\x6A',
    '\xE7\x57' : u'\x1E\x86', '\xE7\x58' : u'\x1E\x8A', '\xE7\x59' : u'\x1E\x8E',
    '\xE7\x5A' : u'\x01\x7B', '\xE7\x62' : u'\x1E\x03', '\xE7\x63' : u'\x01\x0B',
    '\xE7\x64' : u'\x1E\x0B', '\xE7\x65' : u'\x01\x17', '\xE7\x66' : u'\x1E\x1F',
    '\xE7\x67' : u'\x01\x21', '\xE7\x68' : u'\x1E\x23', '\xE7\x6D' : u'\x1E\x41',
    '\xE7\x6E' : u'\x1E\x45', '\xE7\x70' : u'\x1E\x57', '\xE7\x72' : u'\x1E\x59',
    '\xE7\x73' : u'\x1E\x61', '\xE7\x74' : u'\x1E\x6B', '\xE7\x77' : u'\x1E\x87',
    '\xE7\x78' : u'\x1E\x8B', '\xE7\x79' : u'\x1E\x8F', '\xE7\x7A' : u'\x01\x7C',
    '\xE8\x41' : u'\xC4',     '\xE8\x45' : u'\xCB',     '\xE8\x48' : u'\x1E\x26',
    '\xE8\x49' : u'\xCF',     '\xE8\x4F' : u'\xD6',     '\xE8\x55' : u'\xDC',
    '\xE8\x57' : u'\x1E\x84', '\xE8\x58' : u'\x1E\x8C', '\xE8\x59' : u'\x01\x78',
    '\xE8\x61' : u'\xE4',     '\xE8\x65' : u'\xEB',     '\xE8\x68' : u'\x1E\x27',
    '\xE8\x69' : u'\xEF',     '\xE8\x6F' : u'\xF6',     '\xE8\x74' : u'\x1E\x97',
    '\xE8\x75' : u'\xFC',     '\xE8\x77' : u'\x1E\x85', '\xE8\x78' : u'\x1E\x8D',
    '\xE8\x79' : u'\xFF',     '\xE9\x41' : u'\x01\xCD', '\xE9\x43' : u'\x01\x0C',
    '\xE9\x44' : u'\x01\x0E', '\xE9\x45' : u'\x01\x1A', '\xE9\x47' : u'\x01\xE6',
    '\xE9\x49' : u'\x01\xCF', '\xE9\x4B' : u'\x01\xE8', '\xE9\x4C' : u'\x01\x3D',
    '\xE9\x4E' : u'\x01\x47', '\xE9\x4F' : u'\x01\xD1', '\xE9\x52' : u'\x01\x58',
    '\xE9\x53' : u'\x01\x60', '\xE9\x54' : u'\x01\x64', '\xE9\x55' : u'\x01\xD3',
    '\xE9\x5A' : u'\x01\x7D', '\xE9\x61' : u'\x01\xCE', '\xE9\x63' : u'\x01\x0D',
    '\xE9\x64' : u'\x01\x0F', '\xE9\x65' : u'\x01\x1B', '\xE9\x67' : u'\x01\xE7',
    '\xE9\x69' : u'\x01\xD0', '\xE9\x6A' : u'\x01\xF0', '\xE9\x6B' : u'\x01\xE9',
    '\xE9\x6C' : u'\x01\x3E', '\xE9\x6E' : u'\x01\x48', '\xE9\x6F' : u'\x01\xD2',
    '\xE9\x72' : u'\x01\x59', '\xE9\x73' : u'\x01\x61', '\xE9\x74' : u'\x01\x65',
    '\xE9\x75' : u'\x01\xD4', '\xE9\x7A' : u'\x01\x7E', '\xEA\x41' : u'\xC5',
    '\xEA\x61' : u'\xE5',     '\xEA\x75' : u'\x01\x6F', '\xEA\x77' : u'\x1E\x98',
    '\xEA\x79' : u'\x1E\x99', '\xEA\xAD' : u'\x01\x6E', '\xEE\x4F' : u'\x01\x50',
    '\xEE\x55' : u'\x01\x70', '\xEE\x6F' : u'\x01\x51', '\xEE\x75' : u'\x01\x71',
    '\xF0\x20' : u'\xB8',     '\xF0\x43' : u'\xC7',     '\xF0\x44' : u'\x1E\x10',
    '\xF0\x47' : u'\x01\x22', '\xF0\x48' : u'\x1E\x28', '\xF0\x4B' : u'\x01\x36',
    '\xF0\x4C' : u'\x01\x3B', '\xF0\x4E' : u'\x01\x45', '\xF0\x52' : u'\x01\x56',
    '\xF0\x53' : u'\x01\x5E', '\xF0\x54' : u'\x01\x62', '\xF0\x63' : u'\xE7',
    '\xF0\x64' : u'\x1E\x11', '\xF0\x67' : u'\x01\x23', '\xF0\x68' : u'\x1E\x29',
    '\xF0\x6B' : u'\x01\x37', '\xF0\x6C' : u'\x01\x3C', '\xF0\x6E' : u'\x01\x46',
    '\xF0\x72' : u'\x01\x57', '\xF0\x73' : u'\x01\x5F', '\xF0\x74' : u'\x01\x63',
    '\xF1\x41' : u'\x01\x04', '\xF1\x45' : u'\x01\x18', '\xF1\x49' : u'\x01\x2E',
    '\xF1\x4F' : u'\x01\xEA', '\xF1\x55' : u'\x01\x72', '\xF1\x61' : u'\x01\x05',
    '\xF1\x65' : u'\x01\x19', '\xF1\x69' : u'\x01\x2F', '\xF1\x6F' : u'\x01\xEB',
    '\xF1\x75' : u'\x01\x73', '\xF2\x41' : u'\x1E\xA0', '\xF2\x42' : u'\x1E\x04',
    '\xF2\x44' : u'\x1E\x0C', '\xF2\x45' : u'\x1E\xB8', '\xF2\x48' : u'\x1E\x24',
    '\xF2\x49' : u'\x1E\xCA', '\xF2\x4B' : u'\x1E\x32', '\xF2\x4C' : u'\x1E\x36',
    '\xF2\x4D' : u'\x1E\x42', '\xF2\x4E' : u'\x1E\x46', '\xF2\x4F' : u'\x1E\xCC',
    '\xF2\x52' : u'\x1E\x5A', '\xF2\x53' : u'\x1E\x62', '\xF2\x54' : u'\x1E\x6C',
    '\xF2\x55' : u'\x1E\xE4', '\xF2\x56' : u'\x1E\x7E', '\xF2\x57' : u'\x1E\x88',
    '\xF2\x59' : u'\x1E\xF4', '\xF2\x5A' : u'\x1E\x92', '\xF2\x61' : u'\x1E\xA1',
    '\xF2\x62' : u'\x1E\x05', '\xF2\x64' : u'\x1E\x0D', '\xF2\x65' : u'\x1E\xB9',
    '\xF2\x68' : u'\x1E\x25', '\xF2\x69' : u'\x1E\xCB', '\xF2\x6B' : u'\x1E\x33',
    '\xF2\x6C' : u'\x1E\x37', '\xF2\x6D' : u'\x1E\x43', '\xF2\x6E' : u'\x1E\x47',
    '\xF2\x6F' : u'\x1E\xCD', '\xF2\x72' : u'\x1E\x5B', '\xF2\x73' : u'\x1E\x63',
    '\xF2\x74' : u'\x1E\x6D', '\xF2\x75' : u'\x1E\xE5', '\xF2\x76' : u'\x1E\x7F',
    '\xF2\x77' : u'\x1E\x89', '\xF2\x79' : u'\x1E\xF5', '\xF2\x7A' : u'\x1E\x93',
    '\xF3\x55' : u'\x1E\x72', '\xF3\x75' : u'\x1E\x73', '\xF4\x41' : u'\x1E',
    '\xF4\x61' : u'\x1E\x01', '\xF9\x48' : u'\x1E\x2A', '\xF9\x68' : u'\x1E\x2B',
    }


_utoa = {
    u'\xA1' : '\xC6',     u'\xA3' : '\xB9',     u'\xA9' : '\xC3',
    u'\xAE' : '\xAA',     u'\xB0' : '\xC0',     u'\xB1' : '\xAB',
    u'\xB7' : '\xA8',     u'\xB8' : '\xF0\x20', u'\xBF' : '\xC5',
    u'\xC0' : '\xE1\x41', u'\xC1' : '\xE2\x41', u'\xC2' : '\xE3\x41',
    u'\xC3' : '\xE4\x41', u'\xC4' : '\xE8\x41', u'\xC5' : '\xEA\x41',
    u'\xC6' : '\xA5',     u'\xC7' : '\xF0\x43', u'\xC8' : '\xE1\x45',
    u'\xC9' : '\xE2\x45', u'\xCA' : '\xE3\x45', u'\xCB' : '\xE8\x45',
    u'\xCC' : '\xE1\x49', u'\xCD' : '\xE2\x49', u'\xCE' : '\xE3\x49',
    u'\xCF' : '\xE8\x49', u'\xD0' : '\xA3',     u'\xD1' : '\xE4\x4E',
    u'\xD2' : '\xE1\x4F', u'\xD3' : '\xE2\x4F', u'\xD4' : '\xE3\x4F',
    u'\xD5' : '\xE4\x4F', u'\xD6' : '\xE8\x4F', u'\xD8' : '\xA2',
    u'\xD9' : '\xE1\x55', u'\xDA' : '\xE2\x55', u'\xDB' : '\xE3\x55',
    u'\xDC' : '\xE8\x55', u'\xDD' : '\xE2\x59', u'\xDE' : '\xA4',
    u'\xDF' : '\xCF',     u'\xE0' : '\xE1\x61', u'\xE1' : '\xE2\x61',
    u'\xE2' : '\xE3\x61', u'\xE3' : '\xE4\x61', u'\xE4' : '\xE8\x61',
    u'\xE5' : '\xEA\x61', u'\xE6' : '\xB5',     u'\xE7' : '\xF0\x63',
    u'\xE8' : '\xE1\x65', u'\xE9' : '\xE2\x65', u'\xEA' : '\xE3\x65',
    u'\xEB' : '\xE8\x65', u'\xEC' : '\xE1\x69', u'\xED' : '\xE2\x69',
    u'\xEE' : '\xE3\x69', u'\xEF' : '\xE8\x69', u'\xF0' : '\xBA',
    u'\xF1' : '\xE4\x6E', u'\xF2' : '\xE1\x6F', u'\xF3' : '\xE2\x6F',
    u'\xF4' : '\xE3\x6F', u'\xF5' : '\xE4\x6F', u'\xF6' : '\xE8\x6F',
    u'\xF8' : '\xB2',     u'\xF9' : '\xE1\x75', u'\xFA' : '\xE2\x75',
    u'\xFB' : '\xE3\x75', u'\xFC' : '\xE8\x75', u'\xFD' : '\xE2\x79',
    u'\xFE' : '\xB4',     u'\xFF' : '\xE8\x79', u'\x01' : '\xE5\x41',
    u'\x01\x01' : '\xE5\x61', u'\x01\x02' : '\xE6\x41', u'\x01\x03' : '\xE6\x61',
    u'\x01\x04' : '\xF1\x41', u'\x01\x05' : '\xF1\x61', u'\x01\x06' : '\xE2\x43',
    u'\x01\x07' : '\xE2\x63', u'\x01\x08' : '\xE3\x43', u'\x01\x09' : '\xE3\x63',
    u'\x01\x0A' : '\xE7\x43', u'\x01\x0B' : '\xE7\x63', u'\x01\x0C' : '\xE9\x43',
    u'\x01\x0D' : '\xE9\x63', u'\x01\x0E' : '\xE9\x44', u'\x01\x0F' : '\xE9\x64',
    u'\x01\x10' : '\xA3',     u'\x01\x11' : '\xB3',     u'\x01\x12' : '\xE5\x45',
    u'\x01\x13' : '\xE5\x65', u'\x01\x14' : '\xE6\x45', u'\x01\x15' : '\xE6\x65',
    u'\x01\x16' : '\xE7\x45', u'\x01\x17' : '\xE7\x65', u'\x01\x18' : '\xF1\x45',
    u'\x01\x19' : '\xF1\x65', u'\x01\x1A' : '\xE9\x45', u'\x01\x1B' : '\xE9\x65',
    u'\x01\x1C' : '\xE3\x47', u'\x01\x1D' : '\xE3\x67', u'\x01\x1E' : '\xE6\x47',
    u'\x01\x1F' : '\xE6\x67', u'\x01\x20' : '\xE7\x47', u'\x01\x21' : '\xE7\x67',
    u'\x01\x22' : '\xF0\x47', u'\x01\x23' : '\xF0\x67', u'\x01\x24' : '\xE3\x48',
    u'\x01\x25' : '\xE3\x68', u'\x01\x28' : '\xE4\x49', u'\x01\x29' : '\xE4\x69',
    u'\x01\x2A' : '\xE5\x49', u'\x01\x2B' : '\xE5\x69', u'\x01\x2C' : '\xE6\x49',
    u'\x01\x2D' : '\xE6\x69', u'\x01\x2E' : '\xF1\x49', u'\x01\x2F' : '\xF1\x69',
    u'\x01\x30' : '\xE7\x49', u'\x01\x31' : '\xB8',     u'\x01\x34' : '\xE3\x4A',
    u'\x01\x35' : '\xE3\x6A', u'\x01\x36' : '\xF0\x4B', u'\x01\x37' : '\xF0\x6B',
    u'\x01\x39' : '\xE2\x4C', u'\x01\x3A' : '\xE2\x6C', u'\x01\x3B' : '\xF0\x4C',
    u'\x01\x3C' : '\xF0\x6C', u'\x01\x3D' : '\xE9\x4C', u'\x01\x3E' : '\xE9\x6C',
    u'\x01\x41' : '\xA1',     u'\x01\x42' : '\xB1',     u'\x01\x43' : '\xE2\x4E',
    u'\x01\x44' : '\xE2\x6E', u'\x01\x45' : '\xF0\x4E', u'\x01\x46' : '\xF0\x6E',
    u'\x01\x47' : '\xE9\x4E', u'\x01\x48' : '\xE9\x6E', u'\x01\x4C' : '\xE5\x4F',
    u'\x01\x4D' : '\xE5\x6F', u'\x01\x4E' : '\xE6\x4F', u'\x01\x4F' : '\xE6\x6F',
    u'\x01\x50' : '\xEE\x4F', u'\x01\x51' : '\xEE\x6F', u'\x01\x52' : '\xA6',
    u'\x01\x53' : '\xB6',     u'\x01\x54' : '\xE2\x52', u'\x01\x55' : '\xE2\x72',
    u'\x01\x56' : '\xF0\x52', u'\x01\x57' : '\xF0\x72', u'\x01\x58' : '\xE9\x52',
    u'\x01\x59' : '\xE9\x72', u'\x01\x5A' : '\xE2\x53', u'\x01\x5B' : '\xE2\x73',
    u'\x01\x5C' : '\xE3\x53', u'\x01\x5D' : '\xE3\x73', u'\x01\x5E' : '\xF0\x53',
    u'\x01\x5F' : '\xF0\x73', u'\x01\x60' : '\xE9\x53', u'\x01\x61' : '\xE9\x73',
    u'\x01\x62' : '\xF0\x54', u'\x01\x63' : '\xF0\x74', u'\x01\x64' : '\xE9\x54',
    u'\x01\x65' : '\xE9\x74', u'\x01\x68' : '\xE4\x55', u'\x01\x69' : '\xE4\x75',
    u'\x01\x6A' : '\xE5\x55', u'\x01\x6B' : '\xE5\x75', u'\x01\x6C' : '\xE6\x55',
    u'\x01\x6D' : '\xE6\x75', u'\x01\x6E' : '\xEA\xAD', u'\x01\x6F' : '\xEA\x75',
    u'\x01\x70' : '\xEE\x55', u'\x01\x71' : '\xEE\x75', u'\x01\x72' : '\xF1\x55',
    u'\x01\x73' : '\xF1\x75', u'\x01\x74' : '\xE3\x57', u'\x01\x75' : '\xE3\x77',
    u'\x01\x76' : '\xE3\x59', u'\x01\x77' : '\xE3\x79', u'\x01\x78' : '\xE8\x59',
    u'\x01\x79' : '\xE2\x5A', u'\x01\x7A' : '\xE2\x7A', u'\x01\x7B' : '\xE7\x5A',
    u'\x01\x7C' : '\xE7\x7A', u'\x01\x7D' : '\xE9\x5A', u'\x01\x7E' : '\xE9\x7A',
    u'\x01\xA0' : '\xAC',     u'\x01\xA1' : '\xBC',     u'\x01\xAF' : '\xAD',
    u'\x01\xB0' : '\xBD',     u'\x01\xCD' : '\xE9\x41', u'\x01\xCE' : '\xE9\x61',
    u'\x01\xCF' : '\xE9\x49', u'\x01\xD0' : '\xE9\x69', u'\x01\xD1' : '\xE9\x4F',
    u'\x01\xD2' : '\xE9\x6F', u'\x01\xD3' : '\xE9\x55', u'\x01\xD4' : '\xE9\x75',
    u'\x01\xE2' : '\xE5\xA5', u'\x01\xE3' : '\xE5\xB5', u'\x01\xE6' : '\xE9\x47',
    u'\x01\xE7' : '\xE9\x67', u'\x01\xE8' : '\xE9\x4B', u'\x01\xE9' : '\xE9\x6B',
    u'\x01\xEA' : '\xF1\x4F', u'\x01\xEB' : '\xF1\x6F', u'\x01\xF0' : '\xE9\x6A',
    u'\x01\xF4' : '\xE2\x47', u'\x01\xF5' : '\xE2\x67', u'\x01\xFC' : '\xE2\xA5',
    u'\x01\xFD' : '\xE2\xB5', u'\x02\xB9' : '\xA7',     u'\x02\xBA' : '\xB7',
    u'\x02\xBE' : '\xAE',     u'\x02\xBF' : '\xB0',     u'\x03' : '\xE1',
    u'\x03\x01' : '\xE2',     u'\x03\x02' : '\xE3',     u'\x03\x03' : '\xE4',
    u'\x03\x04' : '\xE5',     u'\x03\x06' : '\xE6',     u'\x03\x07' : '\xE7',
    u'\x03\x09' : '\xE0',     u'\x03\x0A' : '\xEA',     u'\x03\x0B' : '\xEE',
    u'\x03\x0C' : '\xE9',     u'\x03\x10' : '\xEF',     u'\x03\x13' : '\xFE',
    u'\x03\x15' : '\xED',     u'\x03\x1C' : '\xF8',     u'\x03\x23' : '\xF2',
    u'\x03\x24' : '\xF3',     u'\x03\x25' : '\xF4',     u'\x03\x26' : '\xF7',
    u'\x03\x27' : '\xF0',     u'\x03\x28' : '\xF1',     u'\x03\x2E' : '\xF9',
    u'\x03\x32' : '\xF6',     u'\x03\x33' : '\xF5',     u'\x1E' : '\xF4\x41',
    u'\x1E\x01' : '\xF4\x61', u'\x1E\x02' : '\xE7\x42', u'\x1E\x03' : '\xE7\x62',
    u'\x1E\x04' : '\xF2\x42', u'\x1E\x05' : '\xF2\x62', u'\x1E\x0A' : '\xE7\x44',
    u'\x1E\x0B' : '\xE7\x64', u'\x1E\x0C' : '\xF2\x44', u'\x1E\x0D' : '\xF2\x64',
    u'\x1E\x10' : '\xF0\x44', u'\x1E\x11' : '\xF0\x64', u'\x1E\x1E' : '\xE7\x46',
    u'\x1E\x1F' : '\xE7\x66', u'\x1E\x20' : '\xE5\x47', u'\x1E\x21' : '\xE5\x67',
    u'\x1E\x22' : '\xE7\x48', u'\x1E\x23' : '\xE7\x68', u'\x1E\x24' : '\xF2\x48',
    u'\x1E\x25' : '\xF2\x68', u'\x1E\x26' : '\xE8\x48', u'\x1E\x27' : '\xE8\x68',
    u'\x1E\x28' : '\xF0\x48', u'\x1E\x29' : '\xF0\x68', u'\x1E\x2A' : '\xF9\x48',
    u'\x1E\x2B' : '\xF9\x68', u'\x1E\x30' : '\xE2\x4B', u'\x1E\x31' : '\xE2\x6B',
    u'\x1E\x32' : '\xF2\x4B', u'\x1E\x33' : '\xF2\x6B', u'\x1E\x36' : '\xF2\x4C',
    u'\x1E\x37' : '\xF2\x6C', u'\x1E\x3E' : '\xE2\x4D', u'\x1E\x3F' : '\xE2\x6D',
    u'\x1E\x40' : '\xE7\x4D', u'\x1E\x41' : '\xE7\x6D', u'\x1E\x42' : '\xF2\x4D',
    u'\x1E\x43' : '\xF2\x6D', u'\x1E\x44' : '\xE7\x4E', u'\x1E\x45' : '\xE7\x6E',
    u'\x1E\x46' : '\xF2\x4E', u'\x1E\x47' : '\xF2\x6E', u'\x1E\x54' : '\xE2\x50',
    u'\x1E\x55' : '\xE2\x70', u'\x1E\x56' : '\xE7\x50', u'\x1E\x57' : '\xE7\x70',
    u'\x1E\x58' : '\xE7\x52', u'\x1E\x59' : '\xE7\x72', u'\x1E\x5A' : '\xF2\x52',
    u'\x1E\x5B' : '\xF2\x72', u'\x1E\x60' : '\xE7\x53', u'\x1E\x61' : '\xE7\x73',
    u'\x1E\x62' : '\xF2\x53', u'\x1E\x63' : '\xF2\x73', u'\x1E\x6A' : '\xE7\x54',
    u'\x1E\x6B' : '\xE7\x74', u'\x1E\x6C' : '\xF2\x54', u'\x1E\x6D' : '\xF2\x74',
    u'\x1E\x72' : '\xF3\x55', u'\x1E\x73' : '\xF3\x75', u'\x1E\x7C' : '\xE4\x56',
    u'\x1E\x7D' : '\xE4\x76', u'\x1E\x7E' : '\xF2\x56', u'\x1E\x7F' : '\xF2\x76',
    u'\x1E\x80' : '\xE1\x57', u'\x1E\x81' : '\xE1\x77', u'\x1E\x82' : '\xE2\x57',
    u'\x1E\x83' : '\xE2\x77', u'\x1E\x84' : '\xE8\x57', u'\x1E\x85' : '\xE8\x77',
    u'\x1E\x86' : '\xE7\x57', u'\x1E\x87' : '\xE7\x77', u'\x1E\x88' : '\xF2\x57',
    u'\x1E\x89' : '\xF2\x77', u'\x1E\x8A' : '\xE7\x58', u'\x1E\x8B' : '\xE7\x78',
    u'\x1E\x8C' : '\xE8\x58', u'\x1E\x8D' : '\xE8\x78', u'\x1E\x8E' : '\xE7\x59',
    u'\x1E\x8F' : '\xE7\x79', u'\x1E\x90' : '\xE3\x5A', u'\x1E\x91' : '\xE3\x7A',
    u'\x1E\x92' : '\xF2\x5A', u'\x1E\x93' : '\xF2\x7A', u'\x1E\x97' : '\xE8\x74',
    u'\x1E\x98' : '\xEA\x77', u'\x1E\x99' : '\xEA\x79', u'\x1E\xA0' : '\xF2\x41',
    u'\x1E\xA1' : '\xF2\x61', u'\x1E\xA2' : '\xE0\x41', u'\x1E\xA3' : '\xE0\x61',
    u'\x1E\xB8' : '\xF2\x45', u'\x1E\xB9' : '\xF2\x65', u'\x1E\xBA' : '\xE0\x45',
    u'\x1E\xBB' : '\xE0\x65', u'\x1E\xBC' : '\xE4\x45', u'\x1E\xBD' : '\xE4\x65',
    u'\x1E\xC8' : '\xE0\x49', u'\x1E\xC9' : '\xE0\x69', u'\x1E\xCA' : '\xF2\x49',
    u'\x1E\xCB' : '\xF2\x69', u'\x1E\xCC' : '\xF2\x4F', u'\x1E\xCD' : '\xF2\x6F',
    u'\x1E\xCE' : '\xE0\x4F', u'\x1E\xCF' : '\xE0\x6F', u'\x1E\xE4' : '\xF2\x55',
    u'\x1E\xE5' : '\xF2\x75', u'\x1E\xE6' : '\xE0\x55', u'\x1E\xE7' : '\xE0\x75',
    u'\x1E\xF2' : '\xE1\x59', u'\x1E\xF3' : '\xE1\x79', u'\x1E\xF4' : '\xF2\x59',
    u'\x1E\xF5' : '\xF2\x79', u'\x1E\xF6' : '\xE0\x59', u'\x1E\xF7' : '\xE0\x79',
    u'\x1E\xF8' : '\xE4\x59', u'\x1E\xF9' : '\xE4\x79',
#    u'\x20\x0C' : '\x8E',     u'\x20\x0D' : '\x8D',     u'\x21\x13' : '\xC1',
#    u'\x21\x17' : '\xC2',     u'\x26\x6D' : '\xA9',     u'\x26\x6F' : '\xC4',
    u'\xFE\x20' : '\xEB',
    u'\xFE\x21' : '\xEC',     u'\xFE\x22' : '\xFA',     u'\xFE\x23' : '\xFB',
    }

def ansel_to_utf8(s):
    """Converts an ANSEL encoded string to UTF8"""

    buff = cStringIO.StringIO()
    while s:
        c0 = ord(s[0])
        if c0 <= 31:
            head = u' '
            s = s[1:]
        elif c0 > 127:
            l2 = s[0:2]
            l1 = s[0]
            if _twobyte.has_key(l2):
                head = _twobyte[l2]
                s = s[2:]
            elif _onebyte.has_key(l1):
                head = _onebyte[l1]
                s = s[1:]
            else:
                head = u'\xff\xfd'
                s = s[1:]
        else:
            head = s[0]
            s = s[1:]
        buff.write(head)
    ans = unicode(buff.getvalue())
    buff.close()
    return ans

def utf8_to_ansel(s):
    """Converts an UTF8 encoded string to ANSEL"""
    
    if type(s) != unicode:
	s = unicode(s)
    buff = cStringIO.StringIO()
    while s:
        c0 = ord(s[0])
        if c0 <= 3 or c0 == 0x1e or c0 >= 0xf3:
            try:
                head = _utoa[s[0:2]]
                s = s[2:]
            except:
		try:
		    head = _utoa[s[0:1]]
		    s = s[1:]
		except:
		    head = '?'
		    s = s[1:]
        elif c0 > 127:
            try:
                head = _utoa[s[0:1]]
                s = s[1:]
            except:
                head = '?'
                s = s[1:]
        else:
            head = s[0]
            s = s[1:]
        buff.write(head)
    ans = buff.getvalue()
    buff.close()
    return ans
