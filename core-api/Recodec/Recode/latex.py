# Conversion of files between different charsets and surfaces.
# Copyright � 1990, 93, 97, 98, 99, 00, 02 Free Software Foundation, Inc.
# Contributed by Fran�ois Pinard <pinard@iro.umontreal.ca>, 1988.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with the `recode' Library; see the file `COPYING.LIB'.
# If not, write to the Free Software Foundation, Inc., 59 Temple Place -
# Suite 330, Boston, MA 02111-1307, USA.

import recode

declares = [('LaTeX', 'TeX', 'ltex')]

# FIXME: Option `-d' is not supported yet.

class Latex(recode.GenericStep):
    internal_coding = 'Latin-1'
    external_coding = 'LaTeX'
    data_diacritics = [
        (192, '\\`A'),                  # capital A with grave accent
        (193, '\\\'A'),                 # capital A with acute accent
        (194, '\\^A'),                  # capital A with circumflex accent
        (195, '\\~A'),                  # capital A with tilde
        (196, '\\"A'),                  # capital A diaeresis
        (197, '\\AA{}'),                # capital A with ring above
        (198, '\\AE{}'),                # capital diphthong A with E
        (199, '\\c{C}'),                # capital C with cedilla
        (200, '\\`E'),                  # capital E with grave accent
        (201, '\\\'E'),                 # capital E with acute accent
        (202, '\\^E'),                  # capital E with circumflex accent
        (203, '\\"E'),                  # capital E with diaeresis
        (204, '\\`I'),                  # capital I with grave accent
        (205, '\\\'I'),                 # capital I with acute accent
        (206, '\\^I'),                  # capital I with circumflex accent
        (207, '\\"I'),                  # capital I with diaeresis
        (209, '\\~N'),                  # capital N with tilde
        (210, '\\`O'),                  # capital O with grave accent
        (211, '\\\'O'),                 # capital O with acute accent
        (212, '\\^O'),                  # capital O with circumflex accent
        (213, '\\~O'),                  # capital O with tilde
        (214, '\\"O'),                  # capital O with diaeresis
        (216, '\\O{}'),                 # capital O with oblique stroke
        (217, '\\`U'),                  # capital U with grave accent
        (218, '\\\'U'),                 # capital U with acute accent
        (219, '\\^U'),                  # capital U with circumflex accent
        (220, '\\"U'),                  # capital U with diaeresis
        (221, '\\\'Y'),                 # capital Y with acute accent
        (223, '\\ss{}'),                # small german sharp s
        (224, '\\`a'),                  # small a with grave accent
        (225, '\\\'a'),                 # small a with acute accent
        (226, '\\^a'),                  # small a with circumflex accent
        (227, '\\~a'),                  # small a with tilde
        (228, '\\"a'),                  # small a with diaeresis
        (229, '\\aa{}'),                # small a with ring above
        (230, '\\ae{}'),                # small diphthong a with e
        (231, '\\c{c}'),                # small c with cedilla
        (232, '\\`e'),                  # small e with grave accent
        (233, '\\\'e'),                 # small e with acute accent
        (234, '\\^e'),                  # small e with circumflex accent
        (235, '\\"e'),                  # small e with diaeresis
        (236, '\\`{\\i}'),              # small i with grave accent
        (237, '\\\'{\\i}'),             # small i with acute accent
        (238, '\\^{\\i}'),              # small i with circumflex accent
        (239, '\\"{\\i}'),              # small i with diaeresis
        (241, '\\~n'),                  # small n with tilde
        (242, '\\`o'),                  # small o with grave accent
        (243, '\\\'o'),                 # small o with acute accent
        (244, '\\^o'),                  # small o with circumflex accent
        (245, '\\~o'),                  # small o with tilde
        (246, '\\"o'),                  # small o with diaeresis
        (248, '\\o{}'),                 # small o with oblique stroke
        (249, '\\`u'),                  # small u with grave accent
        (250, '\\\'u'),                 # small u with acute accent
        (251, '\\^u'),                  # small u with circumflex accent
        (252, '\\"u'),                  # small u with diaeresis
        (253, '\\\'y'),                 # small y with acute accent
        (255, '\\"y'),                  # small y with diaeresis
        ]
    data_others = [
        (35, '\\\#'),
        (36, '\\$'),
        (37, '\\%'),
        (38, '\\&'),
        (92, '\\backslash{}'),
        (95, '\\_'),
        (123, '\\{'),
        (125, '\\}'),
        (160, '~'),                     # no-break space
        (161, '!`'),                    # inverted exclamation mark
        (163, '\\pound{}'),             # pound sign
        (167, '\\S{}'),                 # paragraph sign, section sign
        (168, '\\"{}'),                 # diaeresis
        (169, '\\copyright{}'),         # copyright sign
        (171, '``'),                    # left angle quotation mark
        (172, '\\neg{}'),               # not sign
        (173, '\\-'),                   # soft hyphen
        (176, '\\mbox{$^\\circ$}'),     # degree sign
        (177, '\\mbox{$\\pm$}'),        # plus-minus sign
        (178, '\\mbox{$^2$}'),          # superscript two
        (179, '\\mbox{$^3$}'),          # superscript three
        (180, '\\\'{}'),                # acute accent
        (181, '\\mbox{$\\mu$}'),        # small greek mu, micro sign
        (183, '\\cdotp'),               # middle dot
        (184, '\\,{}'),                 # cedilla
        (185, '\\mbox{$^1$}'),          # superscript one
        (187, '\'\''),                  # right angle quotation mark
        (188, '\\frac1/4{}'),           # vulgar fraction one quarter
        (189, '\\frac1/2{}'),           # vulgar fraction one half
        (190, '\\frac3/4{}'),           # vulgar fraction three quarters
        (191, '?`'),                    # inverted question mark
        ]
    data = data_diacritics + data_others
