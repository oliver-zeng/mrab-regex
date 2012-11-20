import regex
import string
from weakref import proxy
import unittest
import copy
from test.support import run_unittest
import sys

class RegexTests(unittest.TestCase):
    MATCH_CLASS = "<class '_regex.Match'>"
    PATTERN_CLASS = "<class '_regex.Pattern'>"
    FLAGS_WITH_COMPILED_PAT = "can't process flags argument with a compiled pattern"
    INVALID_GROUP_REF = "invalid group reference"
    MISSING_GT = "missing >"
    BAD_GROUP_NAME = "bad group name"
    MISSING_LT = "missing <"
    UNKNOWN_GROUP_I = "unknown group"
    UNKNOWN_GROUP = "unknown group"
    BAD_ESCAPE = "bad escape"
    BAD_OCTAL_ESCAPE = "bad octal escape"
    BAD_SET = "bad set"
    STR_PAT_ON_BYTES = "can't use a string pattern on a bytes-like object"
    BYTES_PAT_ON_STR = "can't use a bytes pattern on a string-like object"
    STR_PAT_BYTES_TEMPL = "sequence item 0: expected str instance, bytes found"
    BYTES_PAT_STR_TEMPL = "sequence item 0: expected bytes, str found"
    BYTES_PAT_UNI_FLAG = "can't use UNICODE flag with a bytes pattern"
    MIXED_FLAGS = "ASCII, LOCALE and UNICODE flags are mutually incompatible"
    MISSING_RPAREN = "missing \\)" # Need to escape parenthesis for unittest.
    TRAILING_CHARS = "trailing characters in pattern"
    BAD_CHAR_RANGE = "bad character range"
    NOTHING_TO_REPEAT = "nothing to repeat"
    OPEN_GROUP = "can't refer to an open group"
    DUPLICATE_GROUP = "duplicate group"
    CANT_TURN_OFF = "bad inline flags: can't turn flags off"
    UNDEF_CHAR_NAME = "undefined character name"

    def test_weakref(self):
        s = 'QabbbcR'
        x = regex.compile('ab+c')
        y = proxy(x)
        if x.findall('QabbbcR') != y.findall('QabbbcR'):
            self.fail()

    def test_search_star_plus(self):
        self.assertEquals(regex.search('a*', 'xxx').span(0), (0, 0))
        self.assertEquals(regex.search('x*', 'axx').span(), (0, 0))
        self.assertEquals(regex.search('x+', 'axx').span(0), (1, 3))
        self.assertEquals(regex.search('x+', 'axx').span(), (1, 3))
        self.assertEquals(regex.search('x', 'aaa'), None)
        self.assertEquals(regex.match('a*', 'xxx').span(0), (0, 0))
        self.assertEquals(regex.match('a*', 'xxx').span(), (0, 0))
        self.assertEquals(regex.match('x*', 'xxxa').span(0), (0, 3))
        self.assertEquals(regex.match('x*', 'xxxa').span(), (0, 3))
        self.assertEquals(regex.match('a+', 'xxx'), None)

    def bump_num(self, matchobj):
        int_value = int(matchobj[0])
        return str(int_value + 1)

    def test_basic_regex_sub(self):
        self.assertEquals(regex.sub("(?i)b+", "x", "bbbb BBBB"), 'x x')
        self.assertEquals(regex.sub(r'\d+', self.bump_num, '08.2 -2 23x99y'),
          '9.3 -3 24x100y')
        self.assertEquals(regex.sub(r'\d+', self.bump_num, '08.2 -2 23x99y',
          3), '9.3 -3 23x99y')

        self.assertEquals(regex.sub('.', lambda m: r"\n", 'x'), "\\n")
        self.assertEquals(regex.sub('.', r"\n", 'x'), "\n")

        self.assertEquals(regex.sub('(?P<a>x)', r'\g<a>\g<a>', 'xx'), 'xxxx')
        self.assertEquals(regex.sub('(?P<a>x)', r'\g<a>\g<1>', 'xx'), 'xxxx')
        self.assertEquals(regex.sub('(?P<unk>x)', r'\g<unk>\g<unk>', 'xx'),
          'xxxx')
        self.assertEquals(regex.sub('(?P<unk>x)', r'\g<1>\g<1>', 'xx'), 'xxxx')

        self.assertEquals(regex.sub('a', r'\t\n\v\r\f\a\b\B\Z\a\A\w\W\s\S\d\D',
          'a'), "\t\n\v\r\f\a\b\\B\\Z\a\\A\\w\\W\\s\\S\\d\\D")
        self.assertEquals(regex.sub('a', '\t\n\v\r\f\a', 'a'), "\t\n\v\r\f\a")
        self.assertEquals(regex.sub('a', '\t\n\v\r\f\a', 'a'), chr(9) + chr(10)
          + chr(11) + chr(13) + chr(12) + chr(7))

        self.assertEquals(regex.sub(r'^\s*', 'X', 'test'), 'Xtest')

        self.assertEquals(regex.sub(r"x", r"\x0A", "x"), "\n")
        self.assertEquals(regex.sub(r"x", r"\u000A", "x"), "\n")
        self.assertEquals(regex.sub(r"x", r"\U0000000A", "x"), "\n")
        self.assertEquals(regex.sub(r"x", r"\N{LATIN CAPITAL LETTER A}", "x"),
          "A")

        self.assertEquals(regex.sub(br"x", br"\x0A", b"x"), b"\n")
        self.assertEquals(regex.sub(br"x", br"\u000A", b"x"), b"\\u000A")
        self.assertEquals(regex.sub(br"x", br"\U0000000A", b"x"),
          b"\\U0000000A")
        self.assertEquals(regex.sub(br"x", br"\N{LATIN CAPITAL LETTER A}",
          b"x"), b"\\N{LATIN CAPITAL LETTER A}")

    def test_bug_449964(self):
        # Fails for group followed by other escape.
        self.assertEquals(regex.sub(r'(?P<unk>x)', r'\g<1>\g<1>\b', 'xx'),
          "xx\bxx\b")

    def test_bug_449000(self):
        # Test for sub() on escaped characters.
        self.assertEquals(regex.sub(r'\r\n', r'\n', 'abc\r\ndef\r\n'),
          "abc\ndef\n")
        self.assertEquals(regex.sub('\r\n', r'\n', 'abc\r\ndef\r\n'),
          "abc\ndef\n")
        self.assertEquals(regex.sub(r'\r\n', '\n', 'abc\r\ndef\r\n'),
          "abc\ndef\n")
        self.assertEquals(regex.sub('\r\n', '\n', 'abc\r\ndef\r\n'),
          "abc\ndef\n")

    def test_bug_1661(self):
        # Verify that flags do not get silently ignored with compiled patterns
        pattern = regex.compile('.')
        self.assertRaisesRegex(ValueError, self.FLAGS_WITH_COMPILED_PAT,
          lambda: regex.match(pattern, 'A', regex.I))
        self.assertRaisesRegex(ValueError, self.FLAGS_WITH_COMPILED_PAT,
          lambda: regex.search(pattern, 'A', regex.I))
        self.assertRaisesRegex(ValueError, self.FLAGS_WITH_COMPILED_PAT,
          lambda: regex.findall(pattern, 'A', regex.I))
        self.assertRaisesRegex(ValueError, self.FLAGS_WITH_COMPILED_PAT,
          lambda: regex.compile(pattern, regex.I))

    def test_bug_3629(self):
        # A regex that triggered a bug in the sre-code validator
        self.assertEquals(repr(type(regex.compile("(?P<quote>)(?(quote))"))),
          self.PATTERN_CLASS)

    def test_sub_template_numeric_escape(self):
        # Bug 776311 and friends.
        self.assertEquals(regex.sub('x', r'\0', 'x'), "\0")
        self.assertEquals(regex.sub('x', r'\000', 'x'), "\000")
        self.assertEquals(regex.sub('x', r'\001', 'x'), "\001")
        self.assertEquals(regex.sub('x', r'\008', 'x'), "\0" + "8")
        self.assertEquals(regex.sub('x', r'\009', 'x'), "\0" + "9")
        self.assertEquals(regex.sub('x', r'\111', 'x'), "\111")
        self.assertEquals(regex.sub('x', r'\117', 'x'), "\117")

        self.assertEquals(regex.sub('x', r'\1111', 'x'), "\1111")
        self.assertEquals(regex.sub('x', r'\1111', 'x'), "\111" + "1")

        self.assertEquals(regex.sub('x', r'\00', 'x'), '\x00')
        self.assertEquals(regex.sub('x', r'\07', 'x'), '\x07')
        self.assertEquals(regex.sub('x', r'\08', 'x'), "\0" + "8")
        self.assertEquals(regex.sub('x', r'\09', 'x'), "\0" + "9")
        self.assertEquals(regex.sub('x', r'\0a', 'x'), "\0" + "a")

        self.assertEquals(regex.sub('x', r'\400', 'x'), "\u0100")
        self.assertEquals(regex.sub('x', r'\777', 'x'), "\u01FF")
        self.assertEquals(regex.sub(b'x', br'\400', b'x'), b"\x00")
        self.assertEquals(regex.sub(b'x', br'\777', b'x'), b"\xFF")

        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\1', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\8', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\9', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\11', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\18', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\1a', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\90', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\99', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\118', 'x')) # r'\11' + '8'
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\11a', 'x'))
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\181', 'x')) # r'\18' + '1'
        self.assertRaisesRegex(regex.error, self.INVALID_GROUP_REF, lambda:
          regex.sub('x', r'\800', 'x')) # r'\80' + '0'

        # In Python 2.3 (etc), these loop endlessly in sre_parser.py.
        self.assertEquals(regex.sub('(((((((((((x)))))))))))', r'\11', 'x'),
          'x')
        self.assertEquals(regex.sub('((((((((((y))))))))))(.)', r'\118',
          'xyz'), 'xz8')
        self.assertEquals(regex.sub('((((((((((y))))))))))(.)', r'\11a',
          'xyz'), 'xza')

    def test_qualified_re_sub(self):
        self.assertEquals(regex.sub('a', 'b', 'aaaaa'), 'bbbbb')
        self.assertEquals(regex.sub('a', 'b', 'aaaaa', 1), 'baaaa')

    def test_bug_114660(self):
        self.assertEquals(regex.sub(r'(\S)\s+(\S)', r'\1 \2', 'hello  there'),
          'hello there')

    def test_bug_462270(self):
        # Test for empty sub() behaviour, see SF bug #462270
        self.assertEquals(regex.sub('x*', '-', 'abxd'), '-a-b--d-')
        self.assertEquals(regex.sub('x+', '-', 'abxd'), 'ab-d')

    def test_bug_14462(self):
        # chr(255) is a valid identifier in Python 3.
        group_name = '\xFF'
        self.assertEquals(regex.search(r'(?P<' + group_name + '>a)',
          'abc').group(group_name), 'a')

    def test_symbolic_refs(self):
        self.assertRaisesRegex(regex.error, self.MISSING_GT, lambda:
          regex.sub('(?P<a>x)', r'\g<a', 'xx'))
        self.assertRaisesRegex(regex.error, self.BAD_GROUP_NAME, lambda:
          regex.sub('(?P<a>x)', r'\g<', 'xx'))
        self.assertRaisesRegex(regex.error, self.MISSING_LT, lambda:
          regex.sub('(?P<a>x)', r'\g', 'xx'))
        self.assertRaisesRegex(regex.error, self.BAD_GROUP_NAME, lambda:
          regex.sub('(?P<a>x)', r'\g<a a>', 'xx'))
        self.assertRaisesRegex(regex.error, self.BAD_GROUP_NAME, lambda:
          regex.sub('(?P<a>x)', r'\g<1a1>', 'xx'))
        self.assertRaisesRegex(IndexError, self.UNKNOWN_GROUP_I, lambda:
          regex.sub('(?P<a>x)', r'\g<ab>', 'xx'))

        # The new behaviour of unmatched but valid groups is to treat them like
        # empty matches in the replacement template, like in Perl.
        self.assertEquals(regex.sub('(?P<a>x)|(?P<b>y)', r'\g<b>', 'xx'), '')
        self.assertEquals(regex.sub('(?P<a>x)|(?P<b>y)', r'\2', 'xx'), '')

        # The old behaviour was to raise it as an IndexError.
        self.assertRaisesRegex(regex.error, self.BAD_GROUP_NAME, lambda:
          regex.sub('(?P<a>x)', r'\g<-1>', 'xx'))

    def test_re_subn(self):
        self.assertEquals(regex.subn("(?i)b+", "x", "bbbb BBBB"), ('x x', 2))
        self.assertEquals(regex.subn("b+", "x", "bbbb BBBB"), ('x BBBB', 1))
        self.assertEquals(regex.subn("b+", "x", "xyz"), ('xyz', 0))
        self.assertEquals(regex.subn("b*", "x", "xyz"), ('xxxyxzx', 4))
        self.assertEquals(regex.subn("b*", "x", "xyz", 2), ('xxxyz', 2))

    def test_re_split(self):
        self.assertEquals(regex.split(":", ":a:b::c"), ['', 'a', 'b', '', 'c'])
        self.assertEquals(regex.split(":*", ":a:b::c"), ['', 'a', 'b', 'c'])
        self.assertEquals(regex.split("(:*)", ":a:b::c"), ['', ':', 'a', ':',
          'b', '::', 'c'])
        self.assertEquals(regex.split("(?::*)", ":a:b::c"), ['', 'a', 'b',
          'c'])
        self.assertEquals(regex.split("(:)*", ":a:b::c"), ['', ':', 'a', ':',
          'b', ':', 'c'])
        self.assertEquals(regex.split("([b:]+)", ":a:b::c"), ['', ':', 'a',
          ':b::', 'c'])
        self.assertEquals(regex.split("(b)|(:+)", ":a:b::c"), ['', None, ':',
          'a', None, ':', '', 'b', None, '', None, '::', 'c'])
        self.assertEquals(regex.split("(?:b)|(?::+)", ":a:b::c"), ['', 'a', '',
          '', 'c'])

        self.assertEquals(regex.split("x", "xaxbxc"), ['', 'a', 'b', 'c'])
        self.assertEquals([m for m in regex.splititer("x", "xaxbxc")], ['',
          'a', 'b', 'c'])

        self.assertEquals(regex.split("(?r)x", "xaxbxc"), ['c', 'b', 'a', ''])
        self.assertEquals([m for m in regex.splititer("(?r)x", "xaxbxc")],
          ['c', 'b', 'a', ''])

        self.assertEquals(regex.split("(x)|(y)", "xaxbxc"), ['', 'x', None,
          'a', 'x', None, 'b', 'x', None, 'c'])
        self.assertEquals([m for m in regex.splititer("(x)|(y)", "xaxbxc")],
          ['', 'x', None, 'a', 'x', None, 'b', 'x', None, 'c'])

        self.assertEquals(regex.split("(?r)(x)|(y)", "xaxbxc"), ['c', 'x',
          None, 'b', 'x', None, 'a', 'x', None, ''])
        self.assertEquals([m for m in regex.splititer("(?r)(x)|(y)",
          "xaxbxc")], ['c', 'x', None, 'b', 'x', None, 'a', 'x', None, ''])

        self.assertEquals(regex.split(r"(?V1)\b", "a b c"), ['', 'a', ' ', 'b',
          ' ', 'c', ''])
        self.assertEquals(regex.split(r"(?V1)\m", "a b c"), ['', 'a ', 'b ',
          'c'])
        self.assertEquals(regex.split(r"(?V1)\M", "a b c"), ['a', ' b', ' c',
          ''])

    def test_qualified_re_split(self):
        self.assertEquals(regex.split(":", ":a:b::c", 2), ['', 'a', 'b::c'])
        self.assertEquals(regex.split(':', 'a:b:c:d', 2), ['a', 'b', 'c:d'])
        self.assertEquals(regex.split("(:)", ":a:b::c", 2), ['', ':', 'a', ':',
          'b::c'])
        self.assertEquals(regex.split("(:*)", ":a:b::c", 2), ['', ':', 'a',
          ':', 'b::c'])

    def test_re_findall(self):
        self.assertEquals(regex.findall(":+", "abc"), [])
        self.assertEquals(regex.findall(":+", "a:b::c:::d"), [':', '::',
          ':::'])
        self.assertEquals(regex.findall("(:+)", "a:b::c:::d"), [':', '::',
          ':::'])
        self.assertEquals(regex.findall("(:)(:*)", "a:b::c:::d"), [(':', ''),
          (':', ':'), (':', '::')])

        self.assertEquals(regex.findall(r"\((?P<test>.{0,5}?TEST)\)",
          "(MY TEST)"), ["MY TEST"])
        self.assertEquals(regex.findall(r"\((?P<test>.{0,3}?TEST)\)",
          "(MY TEST)"), ["MY TEST"])
        self.assertEquals(regex.findall(r"\((?P<test>.{0,3}?T)\)", "(MY T)"),
          ["MY T"])

        self.assertEquals(regex.findall(r"[^a]{2}[A-Z]", "\n  S"), ['  S'])
        self.assertEquals(regex.findall(r"[^a]{2,3}[A-Z]", "\n  S"), ['\n  S'])
        self.assertEquals(regex.findall(r"[^a]{2,3}[A-Z]", "\n   S"), ['   S'])

        self.assertEquals(regex.findall(r"X(Y[^Y]+?){1,2}( |Q)+DEF",
          "XYABCYPPQ\nQ DEF"), [('YPPQ\n', ' ')])

        self.assertEquals(regex.findall(r"(\nTest(\n+.+?){0,2}?)?\n+End",
          "\nTest\nxyz\nxyz\nEnd"), [('\nTest\nxyz\nxyz', '\nxyz')])

    def test_bug_117612(self):
        self.assertEquals(regex.findall(r"(a|(b))", "aba"), [('a', ''), ('b',
          'b'), ('a', '')])

    def test_re_match(self):
        self.assertEquals(regex.match('a', 'a')[:], ('a',))
        self.assertEquals(regex.match('(a)', 'a')[:], ('a', 'a'))
        self.assertEquals(regex.match(r'(a)', 'a')[0], 'a')
        self.assertEquals(regex.match(r'(a)', 'a')[1], 'a')
        self.assertEquals(regex.match(r'(a)', 'a').group(1, 1), ('a', 'a'))

        pat = regex.compile('((a)|(b))(c)?')
        self.assertEquals(pat.match('a')[:], ('a', 'a', 'a', None, None))
        self.assertEquals(pat.match('b')[:], ('b', 'b', None, 'b', None))
        self.assertEquals(pat.match('ac')[:], ('ac', 'a', 'a', None, 'c'))
        self.assertEquals(pat.match('bc')[:], ('bc', 'b', None, 'b', 'c'))
        self.assertEquals(pat.match('bc')[:], ('bc', 'b', None, 'b', 'c'))

        # A single group.
        m = regex.match('(a)', 'a')
        self.assertEquals(m.group(), 'a')
        self.assertEquals(m.group(0), 'a')
        self.assertEquals(m.group(1), 'a')
        self.assertEquals(m.group(1, 1), ('a', 'a'))

        pat = regex.compile('(?:(?P<a1>a)|(?P<b2>b))(?P<c3>c)?')
        self.assertEquals(pat.match('a').group(1, 2, 3), ('a', None, None))
        self.assertEquals(pat.match('b').group('a1', 'b2', 'c3'), (None, 'b',
          None))
        self.assertEquals(pat.match('ac').group(1, 'b2', 3), ('a', None, 'c'))

    def test_re_groupref_exists(self):
        self.assertEquals(regex.match(r'^(\()?([^()]+)(?(1)\))$', '(a)')[:],
          ('(a)', '(', 'a'))
        self.assertEquals(regex.match(r'^(\()?([^()]+)(?(1)\))$', 'a')[:],
          ('a', None, 'a'))
        self.assertEquals(regex.match(r'^(\()?([^()]+)(?(1)\))$', 'a)'), None)
        self.assertEquals(regex.match(r'^(\()?([^()]+)(?(1)\))$', '(a'), None)
        self.assertEquals(regex.match('^(?:(a)|c)((?(1)b|d))$', 'ab')[:],
          ('ab', 'a', 'b'))
        self.assertEquals(regex.match('^(?:(a)|c)((?(1)b|d))$', 'cd')[:],
          ('cd', None, 'd'))
        self.assertEquals(regex.match('^(?:(a)|c)((?(1)|d))$', 'cd')[:], ('cd',
          None, 'd'))
        self.assertEquals(regex.match('^(?:(a)|c)((?(1)|d))$', 'a')[:], ('a',
          'a', ''))

        # Tests for bug #1177831: exercise groups other than the first group.
        p = regex.compile('(?P<g1>a)(?P<g2>b)?((?(g2)c|d))')
        self.assertEquals(p.match('abc')[:], ('abc', 'a', 'b', 'c'))
        self.assertEquals(p.match('ad')[:], ('ad', 'a', None, 'd'))
        self.assertEquals(p.match('abd'), None)
        self.assertEquals(p.match('ac'), None)

    def test_re_groupref(self):
        self.assertEquals(regex.match(r'^(\|)?([^()]+)\1$', '|a|')[:], ('|a|',
          '|', 'a'))
        self.assertEquals(regex.match(r'^(\|)?([^()]+)\1?$', 'a')[:], ('a',
          None, 'a'))
        self.assertEquals(regex.match(r'^(\|)?([^()]+)\1$', 'a|'), None)
        self.assertEquals(regex.match(r'^(\|)?([^()]+)\1$', '|a'), None)
        self.assertEquals(regex.match(r'^(?:(a)|c)(\1)$', 'aa')[:], ('aa', 'a',
          'a'))
        self.assertEquals(regex.match(r'^(?:(a)|c)(\1)?$', 'c')[:], ('c', None,
          None))

        self.assertEquals(regex.findall("(?i)(.{1,40}?),(.{1,40}?)(?:;)+(.{1,80}).{1,40}?\\3(\ |;)+(.{1,80}?)\\1",
          "TEST, BEST; LEST ; Lest 123 Test, Best"), [('TEST', ' BEST',
          ' LEST', ' ', '123 ')])

    def test_groupdict(self):
        self.assertEquals(regex.match('(?P<first>first) (?P<second>second)',
          'first second').groupdict(), {'first': 'first', 'second': 'second'})

    def test_expand(self):
        self.assertEquals(regex.match("(?P<first>first) (?P<second>second)",
          "first second").expand(r"\2 \1 \g<second> \g<first>"),
          'second first second first')

    def test_repeat_minmax(self):
        self.assertEquals(regex.match(r"^(\w){1}$", "abc"), None)
        self.assertEquals(regex.match(r"^(\w){1}?$", "abc"), None)
        self.assertEquals(regex.match(r"^(\w){1,2}$", "abc"), None)
        self.assertEquals(regex.match(r"^(\w){1,2}?$", "abc"), None)

        self.assertEquals(regex.match(r"^(\w){3}$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){1,3}$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){1,4}$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){3,4}?$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){3}?$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){1,3}?$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){1,4}?$", "abc")[1], 'c')
        self.assertEquals(regex.match(r"^(\w){3,4}?$", "abc")[1], 'c')

        self.assertEquals(regex.match("^x{1}$", "xxx"), None)
        self.assertEquals(regex.match("^x{1}?$", "xxx"), None)
        self.assertEquals(regex.match("^x{1,2}$", "xxx"), None)
        self.assertEquals(regex.match("^x{1,2}?$", "xxx"), None)

        self.assertEquals(regex.match("^x{1}", "xxx")[0], 'x')
        self.assertEquals(regex.match("^x{1}?", "xxx")[0], 'x')
        self.assertEquals(regex.match("^x{0,1}", "xxx")[0], 'x')
        self.assertEquals(regex.match("^x{0,1}?", "xxx")[0], '')

        self.assertEquals(repr(type(regex.match("^x{3}$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{1,3}$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{1,4}$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{3,4}?$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{3}?$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{1,3}?$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{1,4}?$", "xxx"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match("^x{3,4}?$", "xxx"))),
          self.MATCH_CLASS)

        self.assertEquals(regex.match("^x{}$", "xxx"), None)
        self.assertEquals(repr(type(regex.match("^x{}$", "x{}"))),
          self.MATCH_CLASS)

    def test_getattr(self):
        self.assertEquals(regex.compile("(?i)(a)(b)").pattern, '(?i)(a)(b)')
        self.assertEquals(regex.compile("(?i)(a)(b)").flags, regex.I | regex.U
          | regex.DEFAULT_VERSION)
        self.assertEquals(regex.compile(b"(?i)(a)(b)").flags, regex.A | regex.I
          | regex.DEFAULT_VERSION)
        self.assertEquals(regex.compile("(?i)(a)(b)").groups, 2)
        self.assertEquals(regex.compile("(?i)(a)(b)").groupindex, {})

        self.assertEquals(regex.compile("(?i)(?P<first>a)(?P<other>b)").groupindex,
          {'first': 1, 'other': 2})

        self.assertEquals(regex.match("(a)", "a").pos, 0)
        self.assertEquals(regex.match("(a)", "a").endpos, 1)

        self.assertEquals(regex.search("b(c)", "abcdef").pos, 0)
        self.assertEquals(regex.search("b(c)", "abcdef").endpos, 6)
        self.assertEquals(regex.search("b(c)", "abcdef").span(), (1, 3))
        self.assertEquals(regex.search("b(c)", "abcdef").span(1), (2, 3))

        self.assertEquals(regex.match("(a)", "a").string, 'a')
        self.assertEquals(regex.match("(a)", "a").regs, ((0, 1), (0, 1)))
        self.assertEquals(repr(type(regex.match("(a)", "a").re)),
          self.PATTERN_CLASS)

        # Issue 14260
        p = regex.compile(r'abc(?P<n>def)')
        p.groupindex["n"] = 0
        self.assertEquals(p.groupindex["n"], 1)

    def test_special_escapes(self):
        self.assertEquals(regex.search(r"\b(b.)\b", "abcd abc bcd bx")[1],
          'bx')
        self.assertEquals(regex.search(r"\B(b.)\B", "abc bcd bc abxd")[1],
          'bx')
        self.assertEquals(regex.search(br"\b(b.)\b", b"abcd abc bcd bx",
          regex.LOCALE)[1], b'bx')
        self.assertEquals(regex.search(br"\B(b.)\B", b"abc bcd bc abxd",
          regex.LOCALE)[1], b'bx')
        self.assertEquals(regex.search(r"\b(b.)\b", "abcd abc bcd bx",
          regex.UNICODE)[1], 'bx')
        self.assertEquals(regex.search(r"\B(b.)\B", "abc bcd bc abxd",
          regex.UNICODE)[1], 'bx')

        self.assertEquals(regex.search(r"^abc$", "\nabc\n", regex.M)[0], 'abc')
        self.assertEquals(regex.search(r"^\Aabc\Z$", "abc", regex.M)[0], 'abc')
        self.assertEquals(regex.search(r"^\Aabc\Z$", "\nabc\n", regex.M), None)

        self.assertEquals(regex.search(br"\b(b.)\b", b"abcd abc bcd bx")[1],
          b'bx')
        self.assertEquals(regex.search(br"\B(b.)\B", b"abc bcd bc abxd")[1],
          b'bx')
        self.assertEquals(regex.search(br"^abc$", b"\nabc\n", regex.M)[0],
          b'abc')
        self.assertEquals(regex.search(br"^\Aabc\Z$", b"abc", regex.M)[0],
          b'abc')
        self.assertEquals(regex.search(br"^\Aabc\Z$", b"\nabc\n", regex.M),
          None)

        self.assertEquals(regex.search(r"\d\D\w\W\s\S", "1aa! a")[0], '1aa! a')
        self.assertEquals(regex.search(br"\d\D\w\W\s\S", b"1aa! a",
          regex.LOCALE)[0], b'1aa! a')
        self.assertEquals(regex.search(r"\d\D\w\W\s\S", "1aa! a",
          regex.UNICODE)[0], '1aa! a')

    def test_bigcharset(self):
        self.assertEquals(regex.match(r"([\u2222\u2223])", "\u2222")[1],
          '\u2222')
        self.assertEquals(regex.match(r"([\u2222\u2223])", "\u2222",
          regex.UNICODE)[1], '\u2222')
        self.assertEquals("".join(regex.findall(".",
          "e\xe8\xe9\xea\xeb\u0113\u011b\u0117", flags=regex.UNICODE)),
            'e\xe8\xe9\xea\xeb\u0113\u011b\u0117')
        self.assertEquals("".join(regex.findall(r"[e\xe8\xe9\xea\xeb\u0113\u011b\u0117]",
          "e\xe8\xe9\xea\xeb\u0113\u011b\u0117", flags=regex.UNICODE)),
          'e\xe8\xe9\xea\xeb\u0113\u011b\u0117')
        self.assertEquals("".join(regex.findall(r"e|\xe8|\xe9|\xea|\xeb|\u0113|\u011b|\u0117",
          "e\xe8\xe9\xea\xeb\u0113\u011b\u0117", flags=regex.UNICODE)),
          'e\xe8\xe9\xea\xeb\u0113\u011b\u0117')

    def test_anyall(self):
        self.assertEquals(regex.match("a.b", "a\nb", regex.DOTALL)[0], "a\nb")
        self.assertEquals(regex.match("a.*b", "a\n\nb", regex.DOTALL)[0],
          "a\n\nb")

    def test_non_consuming(self):
        self.assertEquals(regex.match(r"(a(?=\s[^a]))", "a b")[1], 'a')
        self.assertEquals(regex.match(r"(a(?=\s[^a]*))", "a b")[1], 'a')
        self.assertEquals(regex.match(r"(a(?=\s[abc]))", "a b")[1], 'a')
        self.assertEquals(regex.match(r"(a(?=\s[abc]*))", "a bc")[1], 'a')
        self.assertEquals(regex.match(r"(a)(?=\s\1)", "a a")[1], 'a')
        self.assertEquals(regex.match(r"(a)(?=\s\1*)", "a aa")[1], 'a')
        self.assertEquals(regex.match(r"(a)(?=\s(abc|a))", "a a")[1], 'a')

        self.assertEquals(regex.match(r"(a(?!\s[^a]))", "a a")[1], 'a')
        self.assertEquals(regex.match(r"(a(?!\s[abc]))", "a d")[1], 'a')
        self.assertEquals(regex.match(r"(a)(?!\s\1)", "a b")[1], 'a')
        self.assertEquals(regex.match(r"(a)(?!\s(abc|a))", "a b")[1], 'a')

    def test_ignore_case(self):
        self.assertEquals(regex.match("abc", "ABC", regex.I)[0], 'ABC')
        self.assertEquals(regex.match(b"abc", b"ABC", regex.I)[0], b'ABC')

        self.assertEquals(regex.match(r"(a\s[^a]*)", "a bb", regex.I)[1],
          'a bb')
        self.assertEquals(regex.match(r"(a\s[abc])", "a b", regex.I)[1], 'a b')
        self.assertEquals(regex.match(r"(a\s[abc]*)", "a bb", regex.I)[1],
          'a bb')
        self.assertEquals(regex.match(r"((a)\s\2)", "a a", regex.I)[1], 'a a')
        self.assertEquals(regex.match(r"((a)\s\2*)", "a aa", regex.I)[1],
          'a aa')
        self.assertEquals(regex.match(r"((a)\s(abc|a))", "a a", regex.I)[1],
          'a a')
        self.assertEquals(regex.match(r"((a)\s(abc|a)*)", "a aa", regex.I)[1],
          'a aa')

        # Issue #3511.
        self.assertEquals(regex.match(r"[Z-a]", "_").span(), (0, 1))
        self.assertEquals(regex.match(r"(?i)[Z-a]", "_").span(), (0, 1))

        self.assertEquals(repr(type(regex.match(r"(?i)nao", "nAo"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r"(?i)n\xE3o", "n\xC3o"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r"(?i)n\xE3o", "N\xC3O"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r"(?i)s", "\u017F"))),
          self.MATCH_CLASS)

    def test_case_folding(self):
        self.assertEquals(regex.search(r"(?fi)ss", "SS").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)SS", "ss").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)SS",
          "\N{LATIN SMALL LETTER SHARP S}").span(), (0, 1))
        self.assertEquals(regex.search(r"(?fi)\N{LATIN SMALL LETTER SHARP S}",
          "SS").span(), (0, 2))

        self.assertEquals(regex.search(r"(?fi)\N{LATIN SMALL LIGATURE ST}",
          "ST").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)ST",
          "\N{LATIN SMALL LIGATURE ST}").span(), (0, 1))
        self.assertEquals(regex.search(r"(?fi)ST",
          "\N{LATIN SMALL LIGATURE LONG S T}").span(), (0, 1))

        self.assertEquals(regex.search(r"(?fi)SST",
          "\N{LATIN SMALL LETTER SHARP S}t").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)SST",
          "s\N{LATIN SMALL LIGATURE LONG S T}").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)SST",
          "s\N{LATIN SMALL LIGATURE ST}").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)\N{LATIN SMALL LIGATURE ST}",
          "SST").span(), (1, 3))
        self.assertEquals(regex.search(r"(?fi)SST",
          "s\N{LATIN SMALL LIGATURE ST}").span(), (0, 2))

        self.assertEquals(regex.search(r"(?fi)FFI",
          "\N{LATIN SMALL LIGATURE FFI}").span(), (0, 1))
        self.assertEquals(regex.search(r"(?fi)FFI",
          "\N{LATIN SMALL LIGATURE FF}i").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)FFI",
          "f\N{LATIN SMALL LIGATURE FI}").span(), (0, 2))
        self.assertEquals(regex.search(r"(?fi)\N{LATIN SMALL LIGATURE FFI}",
          "FFI").span(), (0, 3))
        self.assertEquals(regex.search(r"(?fi)\N{LATIN SMALL LIGATURE FF}i",
          "FFI").span(), (0, 3))
        self.assertEquals(regex.search(r"(?fi)f\N{LATIN SMALL LIGATURE FI}",
          "FFI").span(), (0, 3))

        sigma = "\u03A3\u03C3\u03C2"
        for ch1 in sigma:
            for ch2 in sigma:
                if not regex.match(r"(?fi)" + ch1, ch2):
                    self.fail()

        self.assertEquals(bool(regex.search(r"(?iV1)ff", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)ff", "\uFB01\uFB00")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)fi", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)fi", "\uFB01\uFB00")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)fffi", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)f\uFB03", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)ff", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)fi", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)fffi", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)f\uFB03", "\uFB00\uFB01")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)f\uFB01", "\uFB00i")),
          True)
        self.assertEquals(bool(regex.search(r"(?iV1)f\uFB01", "\uFB00i")),
          True)

        self.assertEquals(regex.findall(r"(?iV0)\m(?:word){e<=3}\M(?<!\m(?:word){e<=1}\M)",
          "word word2 word word3 word word234 word23 word"), ["word234",
          "word23"])
        self.assertEquals(regex.findall(r"(?iV1)\m(?:word){e<=3}\M(?<!\m(?:word){e<=1}\M)",
          "word word2 word word3 word word234 word23 word"), ["word234",
          "word23"])

        self.assertEquals(regex.search(r"(?fi)a\N{LATIN SMALL LIGATURE FFI}ne",
          "  affine  ").span(), (2, 8))
        self.assertEquals(regex.search(r"(?fi)a(?:\N{LATIN SMALL LIGATURE FFI}|x)ne",
           "  affine  ").span(), (2, 8))
        self.assertEquals(regex.search(r"(?fi)a(?:\N{LATIN SMALL LIGATURE FFI}|xy)ne",
           "  affine  ").span(), (2, 8))
        self.assertEquals(regex.search(r"(?fi)a\L<options>ne", "affine",
          options=["\N{LATIN SMALL LIGATURE FFI}"]).span(), (0, 6))

    def test_category(self):
        self.assertEquals(regex.match(r"(\s)", " ")[1], ' ')

    def test_not_literal(self):
        self.assertEquals(regex.search(r"\s([^a])", " b")[1], 'b')
        self.assertEquals(regex.search(r"\s([^a]*)", " bb")[1], 'bb')

    def test_search_coverage(self):
        self.assertEquals(regex.search(r"\s(b)", " b")[1], 'b')
        self.assertEquals(regex.search(r"a\s", "a ")[0], 'a ')

    def test_re_escape(self):
        p = ""
        self.assertEquals(regex.escape(p), p)
        for i in range(0, 256):
            p += chr(i)
            self.assertEquals(repr(type(regex.match(regex.escape(chr(i)),
              chr(i)))), self.MATCH_CLASS)
            self.assertEquals(regex.match(regex.escape(chr(i)), chr(i)).span(),
              (0, 1))

        pat = regex.compile(regex.escape(p))
        self.assertEquals(pat.match(p).span(), (0, 256))

    def test_re_escape_byte(self):
        p = b""
        self.assertEquals(regex.escape(p), p)
        for i in range(0, 256):
            b = bytes([i])
            p += b
            self.assertEquals(repr(type(regex.match(regex.escape(b), b))),
              self.MATCH_CLASS)
            self.assertEquals(regex.match(regex.escape(b), b).span(), (0, 1))

        pat = regex.compile(regex.escape(p))
        self.assertEquals(pat.match(p).span(), (0, 256))

    def test_constants(self):
        if regex.I != regex.IGNORECASE:
            self.fail()
        if regex.L != regex.LOCALE:
            self.fail()
        if regex.M != regex.MULTILINE:
            self.fail()
        if regex.S != regex.DOTALL:
            self.fail()
        if regex.X != regex.VERBOSE:
            self.fail()

    def test_flags(self):
        for flag in [regex.I, regex.M, regex.X, regex.S, regex.L]:
            self.assertEquals(repr(type(regex.compile('^pattern$', flag))),
              self.PATTERN_CLASS)

    def test_sre_character_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255]:
            self.assertEquals(repr(type(regex.match(r"\%03o" % i, chr(i)))),
              self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"\%03o0" % i, chr(i) +
              "0"))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"\%03o8" % i, chr(i) +
              "8"))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"\x%02x" % i, chr(i)))),
              self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"\x%02x0" % i, chr(i) +
              "0"))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"\x%02xz" % i, chr(i) +
              "z"))), self.MATCH_CLASS)

        self.assertRaisesRegex(regex.error, self.UNKNOWN_GROUP, lambda:
          regex.match(r"\911", ""))

    def test_sre_character_class_literals(self):
        for i in [0, 8, 16, 32, 64, 127, 128, 255]:
            self.assertEquals(repr(type(regex.match(r"[\%03o]" % i, chr(i)))),
              self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"[\%03o0]" % i,
              chr(i)))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"[\%03o8]" % i,
              chr(i)))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"[\x%02x]" % i,
              chr(i)))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"[\x%02x0]" % i,
              chr(i)))), self.MATCH_CLASS)
            self.assertEquals(repr(type(regex.match(r"[\x%02xz]" % i,
              chr(i)))), self.MATCH_CLASS)

        self.assertRaisesRegex(regex.error, self.BAD_OCTAL_ESCAPE, lambda:
              regex.match(r"[\911]", ""))

    def test_bug_113254(self):
        self.assertEquals(regex.match(r'(a)|(b)', 'b').start(1), -1)
        self.assertEquals(regex.match(r'(a)|(b)', 'b').end(1), -1)
        self.assertEquals(regex.match(r'(a)|(b)', 'b').span(1), (-1, -1))

    def test_bug_527371(self):
        # Bug described in patches 527371/672491.
        self.assertEquals(regex.match(r'(a)?a','a').lastindex, None)
        self.assertEquals(regex.match(r'(a)(b)?b','ab').lastindex, 1)
        self.assertEquals(regex.match(r'(?P<a>a)(?P<b>b)?b','ab').lastgroup,
          'a')
        self.assertEquals(regex.match("(?P<a>a(b))", "ab").lastgroup, 'a')
        self.assertEquals(regex.match("((a))", "a").lastindex, 1)

    def test_bug_545855(self):
        # Bug 545855 -- This pattern failed to cause a compile error as it
        # should, instead provoking a TypeError.
        self.assertRaisesRegex(regex.error, self.BAD_SET, lambda:
          regex.compile('foo[a-'))

    def test_bug_418626(self):
        # Bugs 418626 at al. -- Testing Greg Chapman's addition of op code
        # SRE_OP_MIN_REPEAT_ONE for eliminating recursion on simple uses of
        # pattern '*?' on a long string.
        self.assertEquals(regex.match('.*?c', 10000 * 'ab' + 'cd').end(0),
          20001)
        self.assertEquals(regex.match('.*?cd', 5000 * 'ab' + 'c' + 5000 * 'ab'
          + 'cde').end(0), 20003)
        self.assertEquals(regex.match('.*?cd', 20000 * 'abc' + 'de').end(0),
          60001)
        # Non-simple '*?' still used to hit the recursion limit, before the
        # non-recursive scheme was implemented.
        self.assertEquals(regex.search('(a|b)*?c', 10000 * 'ab' + 'cd').end(0),
          20001)

    def test_bug_612074(self):
        pat = "[" + regex.escape("\u2039") + "]"
        self.assertEquals(regex.compile(pat) and 1, 1)

    def test_stack_overflow(self):
        # Nasty cases that used to overflow the straightforward recursive
        # implementation of repeated groups.
        self.assertEquals(regex.match('(x)*', 50000 * 'x')[1], 'x')
        self.assertEquals(regex.match('(x)*y', 50000 * 'x' + 'y')[1], 'x')
        self.assertEquals(regex.match('(x)*?y', 50000 * 'x' + 'y')[1], 'x')

    def test_scanner(self):
        def s_ident(scanner, token): return token
        def s_operator(scanner, token): return "op%s" % token
        def s_float(scanner, token): return float(token)
        def s_int(scanner, token): return int(token)

        scanner = regex.Scanner([(r"[a-zA-Z_]\w*", s_ident), (r"\d+\.\d*",
          s_float), (r"\d+", s_int), (r"=|\+|-|\*|/", s_operator), (r"\s+",
            None), ])

        self.assertEquals(repr(type(scanner.scanner.scanner("").pattern)),
          self.PATTERN_CLASS)

        self.assertEquals(scanner.scan("sum = 3*foo + 312.50 + bar"), (['sum',
          'op=', 3, 'op*', 'foo', 'op+', 312.5, 'op+', 'bar'], ''))

    def test_bug_448951(self):
        # Bug 448951 (similar to 429357, but with single char match).
        # (Also test greedy matches.)
        for op in '', '?', '*':
            self.assertEquals(regex.match(r'((.%s):)?z' % op, 'z')[:], ('z',
              None, None))
            self.assertEquals(regex.match(r'((.%s):)?z' % op, 'a:z')[:],
              ('a:z', 'a:', 'a'))

    def test_bug_725106(self):
        # Capturing groups in alternatives in repeats.
        self.assertEquals(regex.match('^((a)|b)*', 'abc')[:], ('ab', 'b', 'a'))
        self.assertEquals(regex.match('^(([ab])|c)*', 'abc')[:], ('abc', 'c',
          'b'))
        self.assertEquals(regex.match('^((d)|[ab])*', 'abc')[:], ('ab', 'b',
          None))
        self.assertEquals(regex.match('^((a)c|[ab])*', 'abc')[:], ('ab', 'b',
          None))
        self.assertEquals(regex.match('^((a)|b)*?c', 'abc')[:], ('abc', 'b',
          'a'))
        self.assertEquals(regex.match('^(([ab])|c)*?d', 'abcd')[:], ('abcd',
          'c', 'b'))
        self.assertEquals(regex.match('^((d)|[ab])*?c', 'abc')[:], ('abc', 'b',
          None))
        self.assertEquals(regex.match('^((a)c|[ab])*?c', 'abc')[:], ('abc',
          'b', None))

    def test_bug_725149(self):
        # Mark_stack_base restoring before restoring marks.
        self.assertEquals(regex.match('(a)(?:(?=(b)*)c)*', 'abb')[:], ('a',
          'a', None))
        self.assertEquals(regex.match('(a)((?!(b)*))*', 'abb')[:], ('a', 'a',
          None, None))

    def test_bug_764548(self):
        # Bug 764548, regex.compile() barfs on str/unicode subclasses.
        class my_unicode(str): pass
        pat = regex.compile(my_unicode("abc"))
        self.assertEquals(pat.match("xyz"), None)

    def test_finditer(self):
        it = regex.finditer(r":+", "a:b::c:::d")
        self.assertEquals([item[0] for item in it], [':', '::', ':::'])

    def test_bug_926075(self):
        if regex.compile('bug_926075') is regex.compile(b'bug_926075'):
            self.fail()

    def test_bug_931848(self):
        pattern = "[\u002E\u3002\uFF0E\uFF61]"
        self.assertEquals(regex.compile(pattern).split("a.b.c"), ['a', 'b',
          'c'])

    def test_bug_581080(self):
        it = regex.finditer(r"\s", "a b")
        self.assertEquals(next(it).span(), (1, 2))
        self.assertRaises(StopIteration, lambda: next(it))

        scanner = regex.compile(r"\s").scanner("a b")
        self.assertEquals(scanner.search().span(), (1, 2))
        self.assertEquals(scanner.search(), None)

    def test_bug_817234(self):
        it = regex.finditer(r".*", "asdf")
        self.assertEquals(next(it).span(), (0, 4))
        self.assertEquals(next(it).span(), (4, 4))
        self.assertRaises(StopIteration, lambda: next(it))

    def test_empty_array(self):
        # SF buf 1647541.
        import array
        for typecode in 'bBuhHiIlLfd':
            a = array.array(typecode)
            self.assertEquals(regex.compile(b"bla").match(a), None)
            self.assertEquals(regex.compile(b"").match(a)[1 : ], ())

    def test_inline_flags(self):
        # Bug #1700.
        upper_char = chr(0x1ea0) # Latin Capital Letter A with Dot Below
        lower_char = chr(0x1ea1) # Latin Small Letter A with Dot Below

        p = regex.compile(upper_char, regex.I | regex.U)
        self.assertEquals(repr(type(p.match(lower_char))), self.MATCH_CLASS)

        p = regex.compile(lower_char, regex.I | regex.U)
        self.assertEquals(repr(type(p.match(upper_char))), self.MATCH_CLASS)

        p = regex.compile('(?i)' + upper_char, regex.U)
        self.assertEquals(repr(type(p.match(lower_char))), self.MATCH_CLASS)

        p = regex.compile('(?i)' + lower_char, regex.U)
        self.assertEquals(repr(type(p.match(upper_char))), self.MATCH_CLASS)

        p = regex.compile('(?iu)' + upper_char)
        self.assertEquals(repr(type(p.match(lower_char))), self.MATCH_CLASS)

        p = regex.compile('(?iu)' + lower_char)
        self.assertEquals(repr(type(p.match(upper_char))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r"(?i)a", "A"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r"a(?i)", "A"))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r"(?iV1)a", "A"))),
          self.MATCH_CLASS)
        self.assertEquals(regex.match(r"a(?iV1)", "A"), None)

    def test_dollar_matches_twice(self):
        # $ matches the end of string, and just before the terminating \n.
        pattern = regex.compile('$')
        self.assertEquals(pattern.sub('#', 'a\nb\n'), 'a\nb#\n#')
        self.assertEquals(pattern.sub('#', 'a\nb\nc'), 'a\nb\nc#')
        self.assertEquals(pattern.sub('#', '\n'), '#\n#')

        pattern = regex.compile('$', regex.MULTILINE)
        self.assertEquals(pattern.sub('#', 'a\nb\n' ), 'a#\nb#\n#')
        self.assertEquals(pattern.sub('#', 'a\nb\nc'), 'a#\nb#\nc#')
        self.assertEquals(pattern.sub('#', '\n'), '#\n#')

    def test_bytes_str_mixing(self):
        # Mixing str and bytes is disallowed.
        pat = regex.compile('.')
        bpat = regex.compile(b'.')
        self.assertRaisesRegex(TypeError, self.STR_PAT_ON_BYTES, lambda:
          pat.match(b'b'))
        self.assertRaisesRegex(TypeError, self.BYTES_PAT_ON_STR, lambda:
          bpat.match('b'))
        self.assertRaisesRegex(TypeError, self.STR_PAT_BYTES_TEMPL, lambda:
          pat.sub(b'b', 'c'))
        self.assertRaisesRegex(TypeError, self.STR_PAT_ON_BYTES, lambda:
          pat.sub('b', b'c'))
        self.assertRaisesRegex(TypeError, self.STR_PAT_ON_BYTES, lambda:
          pat.sub(b'b', b'c'))
        self.assertRaisesRegex(TypeError, self.BYTES_PAT_ON_STR, lambda:
          bpat.sub(b'b', 'c'))
        self.assertRaisesRegex(TypeError, self.BYTES_PAT_STR_TEMPL, lambda:
          bpat.sub('b', b'c'))
        self.assertRaisesRegex(TypeError, self.BYTES_PAT_ON_STR, lambda:
          bpat.sub('b', 'c'))

        self.assertRaisesRegex(ValueError, self.BYTES_PAT_UNI_FLAG, lambda:
          regex.compile(b'\w', regex.UNICODE))
        self.assertRaisesRegex(ValueError, self.BYTES_PAT_UNI_FLAG, lambda:
          regex.compile(b'(?u)\w'))
        self.assertRaisesRegex(ValueError, self.MIXED_FLAGS, lambda:
          regex.compile('\w', regex.UNICODE | regex.ASCII))
        self.assertRaisesRegex(ValueError, self.MIXED_FLAGS, lambda:
          regex.compile('(?u)\w', regex.ASCII))
        self.assertRaisesRegex(ValueError, self.MIXED_FLAGS, lambda:
          regex.compile('(?a)\w', regex.UNICODE))
        self.assertRaisesRegex(ValueError, self.MIXED_FLAGS, lambda:
          regex.compile('(?au)\w'))

    def test_ascii_and_unicode_flag(self):
        # String patterns.
        for flags in (0, regex.UNICODE):
            pat = regex.compile('\xc0', flags | regex.IGNORECASE)
            self.assertEquals(repr(type(pat.match('\xe0'))), self.MATCH_CLASS)
            pat = regex.compile('\w', flags)
            self.assertEquals(repr(type(pat.match('\xe0'))), self.MATCH_CLASS)

        pat = regex.compile('\xc0', regex.ASCII | regex.IGNORECASE)
        self.assertEquals(pat.match('\xe0'), None)
        pat = regex.compile('(?a)\xc0', regex.IGNORECASE)
        self.assertEquals(pat.match('\xe0'), None)
        pat = regex.compile('\w', regex.ASCII)
        self.assertEquals(pat.match('\xe0'), None)
        pat = regex.compile('(?a)\w')
        self.assertEquals(pat.match('\xe0'), None)

        # Bytes patterns.
        for flags in (0, regex.ASCII):
            pat = regex.compile(b'\xc0', flags | regex.IGNORECASE)
            self.assertEquals(pat.match(b'\xe0'), None)
            pat = regex.compile(b'\w')
            self.assertEquals(pat.match(b'\xe0'), None)

        self.assertRaisesRegex(ValueError, self.MIXED_FLAGS, lambda:
          regex.compile('(?au)\w'))

    def test_subscripting_match(self):
        m = regex.match(r'(?<a>\w)', 'xy')
        if not m:
            self.fail("Failed: expected match but returned None")
        elif not m or m[0] != m.group(0) or m[1] != m.group(1):
            self.fail("Failed")
        if not m:
            self.fail("Failed: expected match but returned None")
        elif m[:] != ('x', 'x'):
            self.fail("Failed: expected \"('x', 'x')\" but got {} instead".format(ascii(m[:])))

    def test_new_named_groups(self):
        m0 = regex.match(r'(?P<a>\w)', 'x')
        m1 = regex.match(r'(?<a>\w)', 'x')
        if not (m0 and m1 and m0[:] == m1[:]):
            self.fail("Failed")

    def test_properties(self):
        self.assertEquals(regex.match(b'(?ai)\xC0', b'\xE0'), None)
        self.assertEquals(regex.match(br'(?ai)\xC0', b'\xE0'), None)
        self.assertEquals(regex.match(br'(?a)\w', b'\xE0'), None)
        self.assertEquals(repr(type(regex.match(r'\w', '\xE0'))),
          self.MATCH_CLASS)

        self.assertEquals(regex.match(br'(?L)\w', b'\xE0'), None)

        self.assertEquals(repr(type(regex.match(br'(?L)\d', b'0'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(br'(?L)\s', b' '))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(br'(?L)\w', b'a'))),
          self.MATCH_CLASS)
        self.assertEquals(regex.match(br'(?L)\d', b'?'), None)
        self.assertEquals(regex.match(br'(?L)\s', b'?'), None)
        self.assertEquals(regex.match(br'(?L)\w', b'?'), None)

        self.assertEquals(regex.match(br'(?L)\D', b'0'), None)
        self.assertEquals(regex.match(br'(?L)\S', b' '), None)
        self.assertEquals(regex.match(br'(?L)\W', b'a'), None)
        self.assertEquals(repr(type(regex.match(br'(?L)\D', b'?'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(br'(?L)\S', b'?'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(br'(?L)\W', b'?'))),
          self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'\p{Cyrillic}',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{IsCyrillic}',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{Script=Cyrillic}',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{InCyrillic}',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{Block=Cyrillic}',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:Cyrillic:]]',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:IsCyrillic:]]',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:Script=Cyrillic:]]',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:InCyrillic:]]',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:Block=Cyrillic:]]',
          '\N{CYRILLIC CAPITAL LETTER A}'))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'\P{Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\P{IsCyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\P{Script=Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\P{InCyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\P{Block=Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{^Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{^IsCyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{^Script=Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{^InCyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{^Block=Cyrillic}',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:^Cyrillic:]]',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:^IsCyrillic:]]',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:^Script=Cyrillic:]]',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:^InCyrillic:]]',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'[[:^Block=Cyrillic:]]',
          '\N{LATIN CAPITAL LETTER A}'))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'\d', '0'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\s', ' '))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\w', 'A'))),
          self.MATCH_CLASS)
        self.assertEquals(regex.match(r"\d", "?"), None)
        self.assertEquals(regex.match(r"\s", "?"), None)
        self.assertEquals(regex.match(r"\w", "?"), None)
        self.assertEquals(regex.match(r"\D", "0"), None)
        self.assertEquals(regex.match(r"\S", " "), None)
        self.assertEquals(regex.match(r"\W", "A"), None)
        self.assertEquals(repr(type(regex.match(r'\D', '?'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\S', '?'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\W', '?'))),
          self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'\p{L}', 'A'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{L}', 'a'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{Lu}', 'A'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\p{Ll}', 'a'))),
          self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'(?i)a', 'a'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'(?i)a', 'A'))),
          self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match(r'\w', '0'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\w', 'a'))),
          self.MATCH_CLASS)
        self.assertEquals(repr(type(regex.match(r'\w', '_'))),
          self.MATCH_CLASS)

        self.assertEquals(regex.match(r"\X", "\xE0").span(), (0, 1))
        self.assertEquals(regex.match(r"\X", "a\u0300").span(), (0, 2))
        self.assertEquals(regex.findall(r"\X", "a\xE0a\u0300e\xE9e\u0301"),
          ['a', '\xe0', 'a\u0300', 'e', '\xe9', 'e\u0301'])
        self.assertEquals(regex.findall(r"\X{3}", "a\xE0a\u0300e\xE9e\u0301"),
          ['a\xe0a\u0300', 'e\xe9e\u0301'])
        self.assertEquals(regex.findall(r"\X", "\r\r\n\u0301A\u0301"), ['\r',
          '\r\n', '\u0301', 'A\u0301'])

        self.assertEquals(repr(type(regex.match(r'\p{Ll}', 'a'))),
          self.MATCH_CLASS)

        chars_u = "-09AZaz_\u0393\u03b3"
        chars_b = b"-09AZaz_"
        word_set = set("Ll Lm Lo Lt Lu Mc Me Mn Nd Nl No Pc".split())

        tests = [
            (r"\w", chars_u, "09AZaz_\u0393\u03b3"),
            (r"[[:word:]]", chars_u, "09AZaz_\u0393\u03b3"),
            (r"\W", chars_u, "-"),
            (r"[[:^word:]]", chars_u, "-"),
            (r"\d", chars_u, "09"),
            (r"[[:digit:]]", chars_u, "09"),
            (r"\D", chars_u, "-AZaz_\u0393\u03b3"),
            (r"[[:^digit:]]", chars_u, "-AZaz_\u0393\u03b3"),
            (r"[[:alpha:]]", chars_u, "AZaz\u0393\u03b3"),
            (r"[[:^alpha:]]", chars_u, "-09_"),
            (r"[[:alnum:]]", chars_u, "09AZaz\u0393\u03b3"),
            (r"[[:^alnum:]]", chars_u, "-_"),
            (r"[[:xdigit:]]", chars_u, "09Aa"),
            (r"[[:^xdigit:]]", chars_u, "-Zz_\u0393\u03b3"),
            (r"\p{InBasicLatin}", "a\xE1", "a"),
            (r"\P{InBasicLatin}", "a\xE1", "\xE1"),
            (r"(?i)\p{InBasicLatin}", "a\xE1", "a"),
            (r"(?i)\P{InBasicLatin}", "a\xE1", "\xE1"),

            (br"(?L)\w", chars_b, b"09AZaz_"),
            (br"(?L)[[:word:]]", chars_b, b"09AZaz_"),
            (br"(?L)\W", chars_b, b"-"),
            (br"(?L)[[:^word:]]", chars_b, b"-"),
            (br"(?L)\d", chars_b, b"09"),
            (br"(?L)[[:digit:]]", chars_b, b"09"),
            (br"(?L)\D", chars_b, b"-AZaz_"),
            (br"(?L)[[:^digit:]]", chars_b, b"-AZaz_"),
            (br"(?L)[[:alpha:]]", chars_b, b"AZaz"),
            (br"(?L)[[:^alpha:]]", chars_b, b"-09_"),
            (br"(?L)[[:alnum:]]", chars_b, b"09AZaz"),
            (br"(?L)[[:^alnum:]]", chars_b, b"-_"),
            (br"(?L)[[:xdigit:]]", chars_b, b"09Aa"),
            (br"(?L)[[:^xdigit:]]", chars_b, b"-Zz_"),

            (br"(?a)\w", chars_b, b"09AZaz_"),
            (br"(?a)[[:word:]]", chars_b, b"09AZaz_"),
            (br"(?a)\W", chars_b, b"-"),
            (br"(?a)[[:^word:]]", chars_b, b"-"),
            (br"(?a)\d", chars_b, b"09"),
            (br"(?a)[[:digit:]]", chars_b, b"09"),
            (br"(?a)\D", chars_b, b"-AZaz_"),
            (br"(?a)[[:^digit:]]", chars_b, b"-AZaz_"),
            (br"(?a)[[:alpha:]]", chars_b, b"AZaz"),
            (br"(?a)[[:^alpha:]]", chars_b, b"-09_"),
            (br"(?a)[[:alnum:]]", chars_b, b"09AZaz"),
            (br"(?a)[[:^alnum:]]", chars_b, b"-_"),
            (br"(?a)[[:xdigit:]]", chars_b, b"09Aa"),
            (br"(?a)[[:^xdigit:]]", chars_b, b"-Zz_"),
        ]
        for pattern, chars, expected in tests:
            try:
                if chars[ : 0].join(regex.findall(pattern, chars)) != expected:
                    self.fail("Failed: {}".format(pattern))
            except Exception as e:
                self.fail("Failed: {} raised {}".format(pattern, ascii(e)))

        self.assertEquals(bool(regex.match(r"\p{NumericValue=0}", "0")), True)
        self.assertEquals(bool(regex.match(r"\p{NumericValue=1/2}",
          "\N{VULGAR FRACTION ONE HALF}")), True)
        self.assertEquals(bool(regex.match(r"\p{NumericValue=0.5}",
          "\N{VULGAR FRACTION ONE HALF}")), True)

    def test_word_class(self):
        self.assertEquals(regex.findall(r"\w+",
          " \u0939\u093f\u0928\u094d\u0926\u0940,"),
          ['\u0939\u093f\u0928\u094d\u0926\u0940'])
        self.assertEquals(regex.findall(r"\W+",
          " \u0939\u093f\u0928\u094d\u0926\u0940,"), [' ', ','])
        self.assertEquals(regex.split(r"(?V1)\b",
          " \u0939\u093f\u0928\u094d\u0926\u0940,"), [' ',
            '\u0939\u093f\u0928\u094d\u0926\u0940', ','])
        self.assertEquals(regex.split(r"(?V1)\B",
          " \u0939\u093f\u0928\u094d\u0926\u0940,"), ['', ' \u0939', '\u093f',
          '\u0928', '\u094d', '\u0926', '\u0940,', ''])

    def test_search_anchor(self):
        self.assertEquals(regex.findall(r"\G\w{2}", "abcd ef"), ['ab', 'cd'])

    def test_search_reverse(self):
        self.assertEquals(regex.findall(r"(?r).", "abc"), ['c', 'b', 'a'])
        self.assertEquals(regex.findall(r"(?r).", "abc", overlapped=True),
          ['c', 'b', 'a'])
        self.assertEquals(regex.findall(r"(?r)..", "abcde"), ['de', 'bc'])
        self.assertEquals(regex.findall(r"(?r)..", "abcde", overlapped=True),
          ['de', 'cd', 'bc', 'ab'])
        self.assertEquals(regex.findall(r"(?r)(.)(-)(.)", "a-b-c",
          overlapped=True), [("b", "-", "c"), ("a", "-", "b")])

        self.assertEquals([m[0] for m in regex.finditer(r"(?r).", "abc")],
          ['c', 'b', 'a'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)..", "abcde",
          overlapped=True)], ['de', 'cd', 'bc', 'ab'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r).", "abc")],
          ['c', 'b', 'a'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)..", "abcde",
          overlapped=True)], ['de', 'cd', 'bc', 'ab'])

        self.assertEquals(regex.findall(r"^|\w+", "foo bar"), ['', 'foo',
          'bar'])
        self.assertEquals(regex.findall(r"(?V1)^|\w+", "foo bar"), ['', 'foo',
          'bar'])
        self.assertEquals(regex.findall(r"(?r)^|\w+", "foo bar"), ['bar',
          'foo', ''])
        self.assertEquals(regex.findall(r"(?rV1)^|\w+", "foo bar"), ['bar',
          'foo', ''])

        self.assertEquals([m[0] for m in regex.finditer(r"^|\w+", "foo bar")],
          ['', 'foo', 'bar'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?V1)^|\w+",
          "foo bar")], ['', 'foo', 'bar'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)^|\w+",
          "foo bar")], ['bar', 'foo', ''])
        self.assertEquals([m[0] for m in regex.finditer(r"(?rV1)^|\w+",
          "foo bar")], ['bar', 'foo', ''])

        self.assertEquals(regex.findall(r"\G\w{2}", "abcd ef"), ['ab', 'cd'])
        self.assertEquals(regex.findall(r".{2}(?<=\G.*)", "abcd"), ['ab',
          'cd'])
        self.assertEquals(regex.findall(r"(?r)\G\w{2}", "abcd ef"), [])
        self.assertEquals(regex.findall(r"(?r)\w{2}\G", "abcd ef"), ['ef'])

        self.assertEquals(regex.findall(r"q*", "qqwe"), ['qq', '', '', ''])
        self.assertEquals(regex.findall(r"(?V1)q*", "qqwe"), ['qq', '', '',
          ''])
        self.assertEquals(regex.findall(r"(?r)q*", "qqwe"), ['', '', 'qq', ''])
        self.assertEquals(regex.findall(r"(?rV1)q*", "qqwe"), ['', '', 'qq',
          ''])

        self.assertEquals(regex.findall(".", "abcd", pos=1, endpos=3), ['b',
          'c'])
        self.assertEquals(regex.findall(".", "abcd", pos=1, endpos=-1), ['b',
          'c'])
        self.assertEquals([m[0] for m in regex.finditer(".", "abcd", pos=1,
          endpos=3)], ['b', 'c'])
        self.assertEquals([m[0] for m in regex.finditer(".", "abcd", pos=1,
          endpos=-1)], ['b', 'c'])

        self.assertEquals([m[0] for m in regex.finditer("(?r).", "abcd", pos=1,
          endpos=3)], ['c', 'b'])
        self.assertEquals([m[0] for m in regex.finditer("(?r).", "abcd", pos=1,
          endpos=-1)], ['c', 'b'])
        self.assertEquals(regex.findall("(?r).", "abcd", pos=1, endpos=3),
          ['c', 'b'])
        self.assertEquals(regex.findall("(?r).", "abcd", pos=1, endpos=-1),
          ['c', 'b'])

        self.assertEquals(regex.findall(r"[ab]", "aB", regex.I), ['a', 'B'])
        self.assertEquals(regex.findall(r"(?r)[ab]", "aB", regex.I), ['B',
          'a'])

        self.assertEquals(regex.findall(r"(?r).{2}", "abc"), ['bc'])
        self.assertEquals(regex.findall(r"(?r).{2}", "abc", overlapped=True),
          ['bc', 'ab'])
        self.assertEquals(regex.findall(r"(\w+) (\w+)",
          "first second third fourth fifth"), [('first', 'second'), ('third',
          'fourth')])
        self.assertEquals(regex.findall(r"(?r)(\w+) (\w+)",
          "first second third fourth fifth"), [('fourth', 'fifth'), ('second',
          'third')])

        self.assertEquals([m[0] for m in regex.finditer(r"(?r).{2}", "abc")],
          ['bc'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r).{2}", "abc",
          overlapped=True)], ['bc', 'ab'])
        self.assertEquals([m[0] for m in regex.finditer(r"(\w+) (\w+)",
          "first second third fourth fifth")], ['first second',
          'third fourth'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)(\w+) (\w+)",
          "first second third fourth fifth")], ['fourth fifth',
          'second third'])

        self.assertEquals(regex.search("abcdef", "abcdef").span(), (0, 6))
        self.assertEquals(regex.search("(?r)abcdef", "abcdef").span(), (0, 6))
        self.assertEquals(regex.search("(?i)abcdef", "ABCDEF").span(), (0, 6))
        self.assertEquals(regex.search("(?ir)abcdef", "ABCDEF").span(), (0, 6))

        self.assertEquals(regex.sub(r"(.)", r"\1", "abc"), 'abc')
        self.assertEquals(regex.sub(r"(?r)(.)", r"\1", "abc"), 'abc')

    def test_atomic(self):
        # Issue 433030.
        self.assertEquals(regex.search(r"(?>a*)a", "aa"), None)

    def test_possessive(self):
        # Single-character non-possessive.
        self.assertEquals(regex.search(r"a?a", "a").span(), (0, 1))
        self.assertEquals(regex.search(r"a*a", "aaa").span(), (0, 3))
        self.assertEquals(regex.search(r"a+a", "aaa").span(), (0, 3))
        self.assertEquals(regex.search(r"a{1,3}a", "aaa").span(), (0, 3))

        # Multiple-character non-possessive.
        self.assertEquals(regex.search(r"(?:ab)?ab", "ab").span(), (0, 2))
        self.assertEquals(regex.search(r"(?:ab)*ab", "ababab").span(), (0, 6))
        self.assertEquals(regex.search(r"(?:ab)+ab", "ababab").span(), (0, 6))
        self.assertEquals(regex.search(r"(?:ab){1,3}ab", "ababab").span(), (0,
          6))

        # Single-character possessive.
        self.assertEquals(regex.search(r"a?+a", "a"), None)
        self.assertEquals(regex.search(r"a*+a", "aaa"), None)
        self.assertEquals(regex.search(r"a++a", "aaa"), None)
        self.assertEquals(regex.search(r"a{1,3}+a", "aaa"), None)

        # Multiple-character possessive.
        self.assertEquals(regex.search(r"(?:ab)?+ab", "ab"), None)
        self.assertEquals(regex.search(r"(?:ab)*+ab", "ababab"), None)
        self.assertEquals(regex.search(r"(?:ab)++ab", "ababab"), None)
        self.assertEquals(regex.search(r"(?:ab){1,3}+ab", "ababab"), None)

    def test_zerowidth(self):
        # Issue 3262.
        self.assertEquals(regex.split(r"\b", "a b"), ['a b'])
        self.assertEquals(regex.split(r"(?V1)\b", "a b"), ['', 'a', ' ', 'b',
          ''])

        # Issue 1647489.
        self.assertEquals(regex.findall(r"^|\w+", "foo bar"), ['', 'foo',
          'bar'])
        self.assertEquals([m[0] for m in regex.finditer(r"^|\w+", "foo bar")],
          ['', 'foo', 'bar'])
        self.assertEquals(regex.findall(r"(?r)^|\w+", "foo bar"), ['bar',
          'foo', ''])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)^|\w+",
          "foo bar")], ['bar', 'foo', ''])
        self.assertEquals(regex.findall(r"(?V1)^|\w+", "foo bar"), ['', 'foo',
          'bar'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?V1)^|\w+",
          "foo bar")], ['', 'foo', 'bar'])
        self.assertEquals(regex.findall(r"(?rV1)^|\w+", "foo bar"), ['bar',
          'foo', ''])
        self.assertEquals([m[0] for m in regex.finditer(r"(?rV1)^|\w+",
          "foo bar")], ['bar', 'foo', ''])

        self.assertEquals(regex.split("", "xaxbxc"), ['xaxbxc'])
        self.assertEquals([m for m in regex.splititer("", "xaxbxc")],
          ['xaxbxc'])

        self.assertEquals(regex.split("(?r)", "xaxbxc"), ['xaxbxc'])
        self.assertEquals([m for m in regex.splititer("(?r)", "xaxbxc")],
          ['xaxbxc'])

        self.assertEquals(regex.split("(?V1)", "xaxbxc"), ['', 'x', 'a', 'x',
          'b', 'x', 'c', ''])
        self.assertEquals([m for m in regex.splititer("(?V1)", "xaxbxc")], ['',
          'x', 'a', 'x', 'b', 'x', 'c', ''])

        self.assertEquals(regex.split("(?rV1)", "xaxbxc"), ['', 'c', 'x', 'b',
          'x', 'a', 'x', ''])
        self.assertEquals([m for m in regex.splititer("(?rV1)", "xaxbxc")],
          ['', 'c', 'x', 'b', 'x', 'a', 'x', ''])

    def test_scoped_and_inline_flags(self):
        # Issues 433028, #433024, #433027.
        self.assertEquals(regex.search(r"(?i)Ab", "ab").span(), (0, 2))
        self.assertEquals(regex.search(r"(?i:A)b", "ab").span(), (0, 2))
        self.assertEquals(regex.search(r"A(?i)b", "ab").span(), (0, 2))
        self.assertEquals(regex.search(r"A(?iV1)b", "ab"), None)

        self.assertRaisesRegex(regex.error, self.CANT_TURN_OFF, lambda:
          regex.search(r"(?V0-i)Ab", "ab", flags=regex.I))
        self.assertEquals(regex.search(r"(?V1-i)Ab", "ab", flags=regex.I),
          None)
        self.assertEquals(regex.search(r"(?-i:A)b", "ab", flags=regex.I), None)
        self.assertEquals(regex.search(r"A(?V1-i)b", "ab",
          flags=regex.I).span(), (0, 2))

    def test_repeated_repeats(self):
        # Issue 2537.
        self.assertEquals(regex.search(r"(?:a+)+", "aaa").span(), (0, 3))
        self.assertEquals(regex.search(r"(?:(?:ab)+c)+", "abcabc").span(), (0,
          6))

    def test_lookbehind(self):
        self.assertEquals(regex.search(r"123(?<=a\d+)", "a123").span(), (1, 4))
        self.assertEquals(regex.search(r"123(?<=a\d+)", "b123"), None)
        self.assertEquals(regex.search(r"123(?<!a\d+)", "a123"), None)
        self.assertEquals(regex.search(r"123(?<!a\d+)", "b123").span(), (1, 4))

        self.assertEquals(repr(type(regex.match("(a)b(?<=b)(c)", "abc"))),
          self.MATCH_CLASS)
        self.assertEquals(regex.match("(a)b(?<=c)(c)", "abc"), None)
        self.assertEquals(repr(type(regex.match("(a)b(?=c)(c)", "abc"))),
          self.MATCH_CLASS)
        self.assertEquals(regex.match("(a)b(?=b)(c)", "abc"), None)

        self.assertEquals(regex.match("(?:(a)|(x))b(?<=(?(2)x|c))c", "abc"),
          None)
        self.assertEquals(regex.match("(?:(a)|(x))b(?<=(?(2)b|x))c", "abc"),
          None)
        self.assertEquals(repr(type(regex.match("(?:(a)|(x))b(?<=(?(2)x|b))c",
          "abc"))), self.MATCH_CLASS)
        self.assertEquals(regex.match("(?:(a)|(x))b(?<=(?(1)c|x))c", "abc"),
          None)
        self.assertEquals(repr(type(regex.match("(?:(a)|(x))b(?<=(?(1)b|x))c",
          "abc"))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match("(?:(a)|(x))b(?=(?(2)x|c))c",
          "abc"))), self.MATCH_CLASS)
        self.assertEquals(regex.match("(?:(a)|(x))b(?=(?(2)c|x))c", "abc"),
          None)
        self.assertEquals(repr(type(regex.match("(?:(a)|(x))b(?=(?(2)x|c))c",
          "abc"))), self.MATCH_CLASS)
        self.assertEquals(regex.match("(?:(a)|(x))b(?=(?(1)b|x))c", "abc"),
          None)
        self.assertEquals(repr(type(regex.match("(?:(a)|(x))b(?=(?(1)c|x))c",
          "abc"))), self.MATCH_CLASS)

        self.assertEquals(regex.match("(a)b(?<=(?(2)x|c))(c)", "abc"), None)
        self.assertEquals(regex.match("(a)b(?<=(?(2)b|x))(c)", "abc"), None)
        self.assertEquals(regex.match("(a)b(?<=(?(1)c|x))(c)", "abc"), None)
        self.assertEquals(repr(type(regex.match("(a)b(?<=(?(1)b|x))(c)",
          "abc"))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.match("(a)b(?=(?(2)x|c))(c)",
          "abc"))), self.MATCH_CLASS)
        self.assertEquals(regex.match("(a)b(?=(?(2)b|x))(c)", "abc"), None)
        self.assertEquals(repr(type(regex.match("(a)b(?=(?(1)c|x))(c)",
          "abc"))), self.MATCH_CLASS)

        self.assertEquals(repr(type(regex.compile(r"(a)\2(b)"))),
          self.PATTERN_CLASS)

    def test_unmatched_in_sub(self):
        # Issue 1519638.
        self.assertEquals(regex.sub(r"(x)?(y)?", r"\2-\1", "xy"), 'y-x-')
        self.assertEquals(regex.sub(r"(x)?(y)?", r"\2-\1", "x"), '-x-')
        self.assertEquals(regex.sub(r"(x)?(y)?", r"\2-\1", "y"), 'y--')

    def test_bug_10328 (self):
        # Issue 10328.
        pat = regex.compile(r'(?m)(?P<trailing_ws>[ \t]+\r*$)|(?P<no_final_newline>(?<=[^\n])\Z)')
        self.assertEquals(pat.subn(lambda m: '<' + m.lastgroup + '>',
          'foobar '), ('foobar<trailing_ws><no_final_newline>', 2))
        self.assertEquals([m.group() for m in pat.finditer('foobar ')], [' ',
          ''])

    def test_overlapped(self):
        self.assertEquals(regex.findall(r"..", "abcde"), ['ab', 'cd'])
        self.assertEquals(regex.findall(r"..", "abcde", overlapped=True),
          ['ab', 'bc', 'cd', 'de'])
        self.assertEquals(regex.findall(r"(?r)..", "abcde"), ['de', 'bc'])
        self.assertEquals(regex.findall(r"(?r)..", "abcde", overlapped=True),
          ['de', 'cd', 'bc', 'ab'])
        self.assertEquals(regex.findall(r"(.)(-)(.)", "a-b-c",
          overlapped=True), [("a", "-", "b"), ("b", "-", "c")])

        self.assertEquals([m[0] for m in regex.finditer(r"..", "abcde")],
          ['ab', 'cd'])
        self.assertEquals([m[0] for m in regex.finditer(r"..", "abcde",
          overlapped=True)], ['ab', 'bc', 'cd', 'de'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)..", "abcde")],
          ['de', 'bc'])
        self.assertEquals([m[0] for m in regex.finditer(r"(?r)..", "abcde",
          overlapped=True)], ['de', 'cd', 'bc', 'ab'])

        self.assertEquals([m.groups() for m in regex.finditer(r"(.)(-)(.)",
          "a-b-c", overlapped=True)], [("a", "-", "b"), ("b", "-", "c")])
        self.assertEquals([m.groups() for m in regex.finditer(r"(?r)(.)(-)(.)",
          "a-b-c", overlapped=True)], [("b", "-", "c"), ("a", "-", "b")])

    def test_splititer(self):
        self.assertEquals(regex.split(r",", "a,b,,c,"), ['a', 'b', '', 'c',
          ''])
        self.assertEquals([m for m in regex.splititer(r",", "a,b,,c,")], ['a',
          'b', '', 'c', ''])

    def test_grapheme(self):
        self.assertEquals(regex.match(r"\X", "\xE0").span(), (0, 1))
        self.assertEquals(regex.match(r"\X", "a\u0300").span(), (0, 2))

        self.assertEquals(regex.findall(r"\X", "a\xE0a\u0300e\xE9e\u0301"),
          ['a', '\xe0', 'a\u0300', 'e', '\xe9', 'e\u0301'])
        self.assertEquals(regex.findall(r"\X{3}", "a\xE0a\u0300e\xE9e\u0301"),
          ['a\xe0a\u0300', 'e\xe9e\u0301'])
        self.assertEquals(regex.findall(r"\X", "\r\r\n\u0301A\u0301"), ['\r',
          '\r\n', '\u0301', 'A\u0301'])

    def test_word_boundary(self):
        text = 'The quick ("brown") fox can\'t jump 32.3 feet, right?'
        self.assertEquals(regex.split(r'(?V1)\b', text), ['', 'The', ' ',
          'quick', ' ("', 'brown', '") ', 'fox', ' ', 'can', "'", 't', ' ',
          'jump', ' ', '32', '.', '3', ' ', 'feet', ', ', 'right', '?'])
        self.assertEquals(regex.split(r'(?V1w)\b', text), ['', 'The', ' ',
          'quick', ' ', '(', '"', 'brown', '"', ')', ' ', 'fox', ' ', "can't",
          ' ', 'jump', ' ', '32.3', ' ', 'feet', ',', ' ', 'right', '?', ''])

        text = "The  fox"
        self.assertEquals(regex.split(r'(?V1)\b', text), ['', 'The', '  ',
          'fox', ''])
        self.assertEquals(regex.split(r'(?V1w)\b', text), ['', 'The', ' ', ' ',
          'fox', ''])

        text = "can't aujourd'hui l'objectif"
        self.assertEquals(regex.split(r'(?V1)\b', text), ['', 'can', "'", 't',
          ' ', 'aujourd', "'", 'hui', ' ', 'l', "'", 'objectif', ''])
        self.assertEquals(regex.split(r'(?V1w)\b', text), ['', "can't", ' ',
          "aujourd'hui", ' ', "l'", 'objectif', ''])

    def test_line_boundary(self):
        self.assertEquals(regex.findall(r".+", "Line 1\nLine 2\n"), ["Line 1",
          "Line 2"])
        self.assertEquals(regex.findall(r".+", "Line 1\rLine 2\r"),
          ["Line 1\rLine 2\r"])
        self.assertEquals(regex.findall(r".+", "Line 1\r\nLine 2\r\n"),
          ["Line 1\r", "Line 2\r"])
        self.assertEquals(regex.findall(r"(?w).+", "Line 1\nLine 2\n"),
          ["Line 1", "Line 2"])
        self.assertEquals(regex.findall(r"(?w).+", "Line 1\rLine 2\r"),
          ["Line 1", "Line 2"])
        self.assertEquals(regex.findall(r"(?w).+", "Line 1\r\nLine 2\r\n"),
          ["Line 1", "Line 2"])

        self.assertEquals(regex.search(r"^abc", "abc").start(), 0)
        self.assertEquals(regex.search(r"^abc", "\nabc"), None)
        self.assertEquals(regex.search(r"^abc", "\rabc"), None)
        self.assertEquals(regex.search(r"(?w)^abc", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?w)^abc", "\nabc"), None)
        self.assertEquals(regex.search(r"(?w)^abc", "\rabc"), None)

        self.assertEquals(regex.search(r"abc$", "abc").start(), 0)
        self.assertEquals(regex.search(r"abc$", "abc\n").start(), 0)
        self.assertEquals(regex.search(r"abc$", "abc\r"), None)
        self.assertEquals(regex.search(r"(?w)abc$", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?w)abc$", "abc\n").start(), 0)
        self.assertEquals(regex.search(r"(?w)abc$", "abc\r").start(), 0)

        self.assertEquals(regex.search(r"(?m)^abc", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?m)^abc", "\nabc").start(), 1)
        self.assertEquals(regex.search(r"(?m)^abc", "\rabc"), None)
        self.assertEquals(regex.search(r"(?mw)^abc", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?mw)^abc", "\nabc").start(), 1)
        self.assertEquals(regex.search(r"(?mw)^abc", "\rabc").start(), 1)

        self.assertEquals(regex.search(r"(?m)abc$", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?m)abc$", "abc\n").start(), 0)
        self.assertEquals(regex.search(r"(?m)abc$", "abc\r"), None)
        self.assertEquals(regex.search(r"(?mw)abc$", "abc").start(), 0)
        self.assertEquals(regex.search(r"(?mw)abc$", "abc\n").start(), 0)
        self.assertEquals(regex.search(r"(?mw)abc$", "abc\r").start(), 0)

    def test_branch_reset(self):
        self.assertEquals(regex.match(r"(?:(a)|(b))(c)", "ac").groups(), ('a',
          None, 'c'))
        self.assertEquals(regex.match(r"(?:(a)|(b))(c)", "bc").groups(), (None,
          'b', 'c'))
        self.assertEquals(regex.match(r"(?:(?<a>a)|(?<b>b))(?<c>c)",
          "ac").groups(), ('a', None, 'c'))
        self.assertEquals(regex.match(r"(?:(?<a>a)|(?<b>b))(?<c>c)",
          "bc").groups(), (None, 'b', 'c'))

        self.assertEquals(regex.match(r"(?<a>a)(?:(?<b>b)|(?<c>c))(?<d>d)",
          "abd").groups(), ('a', 'b', None, 'd'))
        self.assertEquals(regex.match(r"(?<a>a)(?:(?<b>b)|(?<c>c))(?<d>d)",
          "acd").groups(), ('a', None, 'c', 'd'))
        self.assertEquals(regex.match(r"(a)(?:(b)|(c))(d)", "abd").groups(),
          ('a', 'b', None, 'd'))

        self.assertEquals(regex.match(r"(a)(?:(b)|(c))(d)", "acd").groups(),
          ('a', None, 'c', 'd'))
        self.assertEquals(regex.match(r"(a)(?|(b)|(b))(d)", "abd").groups(),
          ('a', 'b', 'd'))
        self.assertEquals(regex.match(r"(?|(?<a>a)|(?<b>b))(c)",
          "ac").groups(), ('a', None, 'c'))
        self.assertEquals(regex.match(r"(?|(?<a>a)|(?<b>b))(c)",
          "bc").groups(), (None, 'b', 'c'))
        self.assertEquals(regex.match(r"(?|(?<a>a)|(?<a>b))(c)",
          "ac").groups(), ('a', 'c'))

        self.assertEquals(regex.match(r"(?|(?<a>a)|(?<a>b))(c)",
          "bc").groups(), ('b', 'c'))

        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(?<b>c)(?<a>d))(e)",
          "abe").groups(), ('a', 'b', 'e'))
        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(?<b>c)(?<a>d))(e)",
          "cde").groups(), ('d', 'c', 'e'))
        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(?<b>c)(d))(e)",
          "abe").groups(), ('a', 'b', 'e'))
        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(?<b>c)(d))(e)",
          "cde").groups(), ('d', 'c', 'e'))
        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(c)(d))(e)",
          "abe").groups(), ('a', 'b', 'e'))
        self.assertEquals(regex.match(r"(?|(?<a>a)(?<b>b)|(c)(d))(e)",
          "cde").groups(), ('c', 'd', 'e'))
        self.assertRaisesRegex(regex.error, self.DUPLICATE_GROUP, lambda:
          regex.match(r"(?|(?<a>a)(?<b>b)|(c)(?<a>d))(e)", "abe"))
        self.assertRaisesRegex(regex.error, self.DUPLICATE_GROUP, lambda:
          regex.match(r"(?|(?<a>a)(?<b>b)|(c)(?<a>d))(e)", "cde"))

    def test_set(self):
        self.assertEquals(regex.match(r"[a]", "a").span(), (0, 1))
        self.assertEquals(regex.match(r"(?i)[a]", "A").span(), (0, 1))
        self.assertEquals(regex.match(r"[a-b]", r"a").span(), (0, 1))
        self.assertEquals(regex.match(r"(?i)[a-b]", r"A").span(), (0, 1))

        self.assertEquals(regex.sub(r"(?V0)([][])", r"-", "a[b]c"), "a-b-c")

        self.assertEquals(regex.findall(r"[\p{Alpha}]", "a0"), ["a"])
        self.assertEquals(regex.findall(r"(?i)[\p{Alpha}]", "A0"), ["A"])

        self.assertEquals(regex.findall(r"[a\p{Alpha}]", "ab0"), ["a", "b"])
        self.assertEquals(regex.findall(r"[a\P{Alpha}]", "ab0"), ["a", "0"])
        self.assertEquals(regex.findall(r"(?i)[a\p{Alpha}]", "ab0"), ["a",
          "b"])
        self.assertEquals(regex.findall(r"(?i)[a\P{Alpha}]", "ab0"), ["a",
          "0"])

        self.assertEquals(regex.findall(r"[a-b\p{Alpha}]", "abC0"), ["a", "b",
          "C"])
        self.assertEquals(regex.findall(r"(?i)[a-b\p{Alpha}]", "AbC0"), ["A",
          "b", "C"])

        self.assertEquals(regex.findall(r"[\p{Alpha}]", "a0"), ["a"])
        self.assertEquals(regex.findall(r"[\P{Alpha}]", "a0"), ["0"])
        self.assertEquals(regex.findall(r"[^\p{Alpha}]", "a0"), ["0"])
        self.assertEquals(regex.findall(r"[^\P{Alpha}]", "a0"), ["a"])

        self.assertEquals("".join(regex.findall(r"[^\d-h]", "a^b12c-h")),
          'a^bc')
        self.assertEquals("".join(regex.findall(r"[^\dh]", "a^b12c-h")),
          'a^bc-')
        self.assertEquals("".join(regex.findall(r"[^h\s\db]", "a^b 12c-h")),
          'a^c-')
        self.assertEquals("".join(regex.findall(r"[^b\w]", "a b")), ' ')
        self.assertEquals("".join(regex.findall(r"[^b\S]", "a b")), ' ')
        self.assertEquals("".join(regex.findall(r"[^8\d]", "a 1b2")), 'a b')

        all_chars = "".join(chr(c) for c in range(0x100))
        self.assertEquals(len(regex.findall(r"\p{ASCII}", all_chars)), 128)
        self.assertEquals(len(regex.findall(r"\p{Letter}", all_chars)), 117)
        self.assertEquals(len(regex.findall(r"\p{Digit}", all_chars)), 10)

        # Set operators
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}&&\p{Letter}]",
          all_chars)), 52)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}&&\p{Alnum}&&\p{Letter}]",
          all_chars)), 52)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}&&\p{Alnum}&&\p{Digit}]",
          all_chars)), 10)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}&&\p{Cc}]",
          all_chars)), 33)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}&&\p{Graph}]",
          all_chars)), 94)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{ASCII}--\p{Cc}]",
          all_chars)), 95)
        self.assertEquals(len(regex.findall(r"[\p{Letter}\p{Digit}]",
          all_chars)), 127)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{Letter}||\p{Digit}]",
          all_chars)), 127)
        self.assertEquals(len(regex.findall(r"\p{HexDigit}", all_chars)), 22)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{HexDigit}~~\p{Digit}]",
          all_chars)), 12)
        self.assertEquals(len(regex.findall(r"(?V1)[\p{Digit}~~\p{HexDigit}]",
          all_chars)), 12)

        self.assertEquals(repr(type(regex.compile(r"(?V0)([][-])"))),
          self.PATTERN_CLASS)
        self.assertEquals(regex.findall(r"(?V1)[[a-z]--[aei]]", "abc"), ["b",
          "c"])
        self.assertEquals(regex.findall(r"(?iV1)[[a-z]--[aei]]", "abc"), ["b",
          "c"])
        self.assertEquals(regex.findall("(?V1)[\w--a]","abc"), ["b", "c"])
        self.assertEquals(regex.findall("(?iV1)[\w--a]","abc"), ["b", "c"])

    def test_various(self):
        tests = [
            # Test ?P< and ?P= extensions.
            ('(?P<foo_123', '', '', regex.error, self.MISSING_GT),      # Unterminated group identifier.
            ('(?P<1>a)', '', '', regex.error, self.BAD_GROUP_NAME),     # Begins with a digit.
            ('(?P<!>a)', '', '', regex.error, self.BAD_GROUP_NAME),     # Begins with an illegal char.
            ('(?P<foo!>a)', '', '', regex.error, self.BAD_GROUP_NAME),  # Begins with an illegal char.

            # Same tests, for the ?P= form.
            ('(?P<foo_123>a)(?P=foo_123', 'aa', '', regex.error,
              self.MISSING_RPAREN),
            ('(?P<foo_123>a)(?P=1)', 'aa', '', regex.error,
              self.BAD_GROUP_NAME),
            ('(?P<foo_123>a)(?P=!)', 'aa', '', regex.error,
              self.BAD_GROUP_NAME),
            ('(?P<foo_123>a)(?P=foo_124)', 'aa', '', regex.error,
              self.UNKNOWN_GROUP),  # Backref to undefined group.

            ('(?P<foo_123>a)', 'a', '1', ascii('a')),
            ('(?P<foo_123>a)(?P=foo_123)', 'aa', '1', ascii('a')),

            # Mal-formed \g in pattern treated as literal for compatibility.
            (r'(?<foo_123>a)\g<foo_123', 'aa', '', ascii(None)),
            (r'(?<foo_123>a)\g<1>', 'aa', '1', ascii('a')),
            (r'(?<foo_123>a)\g<!>', 'aa', '', ascii(None)),
            (r'(?<foo_123>a)\g<foo_124>', 'aa', '', regex.error,
              self.UNKNOWN_GROUP),  # Backref to undefined group.

            ('(?<foo_123>a)', 'a', '1', ascii('a')),
            (r'(?<foo_123>a)\g<foo_123>', 'aa', '1', ascii('a')),

            # Test octal escapes.
            ('\\1', 'a', '', regex.error, self.UNKNOWN_GROUP),    # Backreference.
            ('[\\1]', '\1', '0', "'\\x01'"),  # Character.
            ('\\09', chr(0) + '9', '0', ascii(chr(0) + '9')),
            ('\\141', 'a', '0', ascii('a')),
            ('(a)(b)(c)(d)(e)(f)(g)(h)(i)(j)(k)(l)\\119', 'abcdefghijklk9',
              '0,11', ascii(('abcdefghijklk9', 'k'))),

            # Test \0 is handled everywhere.
            (r'\0', '\0', '0', ascii('\0')),
            (r'[\0a]', '\0', '0', ascii('\0')),
            (r'[a\0]', '\0', '0', ascii('\0')),
            (r'[^a\0]', '\0', '', ascii(None)),

            # Test various letter escapes.
            (r'\a[\b]\f\n\r\t\v', '\a\b\f\n\r\t\v', '0',
              ascii('\a\b\f\n\r\t\v')),
            (r'[\a][\b][\f][\n][\r][\t][\v]', '\a\b\f\n\r\t\v', '0',
              ascii('\a\b\f\n\r\t\v')),
            (r'\c\e\g\h\i\j\k\o\p\q\y\z', 'ceghijkopqyz', '0',
              ascii('ceghijkopqyz')),
            (r'\xff', '\377', '0', ascii(chr(255))),

            # New \x semantics.
            (r'\x00ffffffffffffff', '\377', '', ascii(None)),
            (r'\x00f', '\017', '', ascii(None)),
            (r'\x00fe', '\376', '', ascii(None)),

            (r'\x00ff', '\377', '', ascii(None)),
            (r'\t\n\v\r\f\a\g', '\t\n\v\r\f\ag', '0', ascii('\t\n\v\r\f\ag')),
            ('\t\n\v\r\f\a\g', '\t\n\v\r\f\ag', '0', ascii('\t\n\v\r\f\ag')),
            (r'\t\n\v\r\f\a', '\t\n\v\r\f\a', '0', ascii(chr(9) + chr(10) +
              chr(11) + chr(13) + chr(12) + chr(7))),
            (r'[\t][\n][\v][\r][\f][\b]', '\t\n\v\r\f\b', '0',
              ascii('\t\n\v\r\f\b')),

            (r"^\w+=(\\[\000-\277]|[^\n\\])*",
              "SRC=eval.c g.c blah blah blah \\\\\n\tapes.c", '0',
              ascii("SRC=eval.c g.c blah blah blah \\\\")),

            # Test that . only matches \n in DOTALL mode.
            ('a.b', 'acb', '0', ascii('acb')),
            ('a.b', 'a\nb', '', ascii(None)),
            ('a.*b', 'acc\nccb', '', ascii(None)),
            ('a.{4,5}b', 'acc\nccb', '', ascii(None)),
            ('a.b', 'a\rb', '0', ascii('a\rb')),
            # The new behaviour is that the inline flag affects only what follows.
            ('a.b(?s)', 'a\nb', '0', ascii('a\nb')),
            ('a.b(?sV1)', 'a\nb', '', ascii(None)),
            ('(?s)a.b', 'a\nb', '0', ascii('a\nb')),
            ('a.*(?s)b', 'acc\nccb', '0', ascii('acc\nccb')),
            ('a.*(?sV1)b', 'acc\nccb', '', ascii(None)),
            ('(?s)a.*b', 'acc\nccb', '0', ascii('acc\nccb')),
            ('(?s)a.{4,5}b', 'acc\nccb', '0', ascii('acc\nccb')),

            (')', '', '', regex.error, self.TRAILING_CHARS),           # Unmatched right bracket.
            ('', '', '0', "''"),    # Empty pattern.
            ('abc', 'abc', '0', ascii('abc')),
            ('abc', 'xbc', '', ascii(None)),
            ('abc', 'axc', '', ascii(None)),
            ('abc', 'abx', '', ascii(None)),
            ('abc', 'xabcy', '0', ascii('abc')),
            ('abc', 'ababc', '0', ascii('abc')),
            ('ab*c', 'abc', '0', ascii('abc')),
            ('ab*bc', 'abc', '0', ascii('abc')),

            ('ab*bc', 'abbc', '0', ascii('abbc')),
            ('ab*bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab+bc', 'abbc', '0', ascii('abbc')),
            ('ab+bc', 'abc', '', ascii(None)),
            ('ab+bc', 'abq', '', ascii(None)),
            ('ab+bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab?bc', 'abbc', '0', ascii('abbc')),
            ('ab?bc', 'abc', '0', ascii('abc')),
            ('ab?bc', 'abbbbc', '', ascii(None)),
            ('ab?c', 'abc', '0', ascii('abc')),

            ('^abc$', 'abc', '0', ascii('abc')),
            ('^abc$', 'abcc', '', ascii(None)),
            ('^abc', 'abcc', '0', ascii('abc')),
            ('^abc$', 'aabc', '', ascii(None)),
            ('abc$', 'aabc', '0', ascii('abc')),
            ('^', 'abc', '0', ascii('')),
            ('$', 'abc', '0', ascii('')),
            ('a.c', 'abc', '0', ascii('abc')),
            ('a.c', 'axc', '0', ascii('axc')),
            ('a.*c', 'axyzc', '0', ascii('axyzc')),

            ('a.*c', 'axyzd', '', ascii(None)),
            ('a[bc]d', 'abc', '', ascii(None)),
            ('a[bc]d', 'abd', '0', ascii('abd')),
            ('a[b-d]e', 'abd', '', ascii(None)),
            ('a[b-d]e', 'ace', '0', ascii('ace')),
            ('a[b-d]', 'aac', '0', ascii('ac')),
            ('a[-b]', 'a-', '0', ascii('a-')),
            ('a[\\-b]', 'a-', '0', ascii('a-')),
            ('a[b-]', 'a-', '0', ascii('a-')),
            ('a[]b', '-', '', regex.error, self.BAD_SET),

            ('a[', '-', '', regex.error, self.BAD_SET),
            ('a\\', '-', '', regex.error, self.BAD_ESCAPE),
            ('abc)', '-', '', regex.error, self.TRAILING_CHARS),
            ('(abc', '-', '', regex.error, self.MISSING_RPAREN),
            ('a]', 'a]', '0', ascii('a]')),
            ('a[]]b', 'a]b', '0', ascii('a]b')),
            ('a[]]b', 'a]b', '0', ascii('a]b')),
            ('a[^bc]d', 'aed', '0', ascii('aed')),
            ('a[^bc]d', 'abd', '', ascii(None)),
            ('a[^-b]c', 'adc', '0', ascii('adc')),

            ('a[^-b]c', 'a-c', '', ascii(None)),
            ('a[^]b]c', 'a]c', '', ascii(None)),
            ('a[^]b]c', 'adc', '0', ascii('adc')),
            ('\\ba\\b', 'a-', '0', ascii('a')),
            ('\\ba\\b', '-a', '0', ascii('a')),
            ('\\ba\\b', '-a-', '0', ascii('a')),
            ('\\by\\b', 'xy', '', ascii(None)),
            ('\\by\\b', 'yz', '', ascii(None)),
            ('\\by\\b', 'xyz', '', ascii(None)),
            ('x\\b', 'xyz', '', ascii(None)),

            ('x\\B', 'xyz', '0', ascii('x')),
            ('\\Bz', 'xyz', '0', ascii('z')),
            ('z\\B', 'xyz', '', ascii(None)),
            ('\\Bx', 'xyz', '', ascii(None)),
            ('\\Ba\\B', 'a-', '', ascii(None)),
            ('\\Ba\\B', '-a', '', ascii(None)),
            ('\\Ba\\B', '-a-', '', ascii(None)),
            ('\\By\\B', 'xy', '', ascii(None)),
            ('\\By\\B', 'yz', '', ascii(None)),
            ('\\By\\b', 'xy', '0', ascii('y')),

            ('\\by\\B', 'yz', '0', ascii('y')),
            ('\\By\\B', 'xyz', '0', ascii('y')),
            ('ab|cd', 'abc', '0', ascii('ab')),
            ('ab|cd', 'abcd', '0', ascii('ab')),
            ('()ef', 'def', '0,1', ascii(('ef', ''))),
            ('$b', 'b', '', ascii(None)),
            ('a\\(b', 'a(b', '', ascii(('a(b',))),
            ('a\\(*b', 'ab', '0', ascii('ab')),
            ('a\\(*b', 'a((b', '0', ascii('a((b')),
            ('a\\\\b', 'a\\b', '0', ascii('a\\b')),

            ('((a))', 'abc', '0,1,2', ascii(('a', 'a', 'a'))),
            ('(a)b(c)', 'abc', '0,1,2', ascii(('abc', 'a', 'c'))),
            ('a+b+c', 'aabbabc', '0', ascii('abc')),
            ('(a+|b)*', 'ab', '0,1', ascii(('ab', 'b'))),
            ('(a+|b)+', 'ab', '0,1', ascii(('ab', 'b'))),
            ('(a+|b)?', 'ab', '0,1', ascii(('a', 'a'))),
            (')(', '-', '', regex.error, self.TRAILING_CHARS),
            ('[^ab]*', 'cde', '0', ascii('cde')),
            ('abc', '', '', ascii(None)),
            ('a*', '', '0', ascii('')),

            ('a|b|c|d|e', 'e', '0', ascii('e')),
            ('(a|b|c|d|e)f', 'ef', '0,1', ascii(('ef', 'e'))),
            ('abcd*efg', 'abcdefg', '0', ascii('abcdefg')),
            ('ab*', 'xabyabbbz', '0', ascii('ab')),
            ('ab*', 'xayabbbz', '0', ascii('a')),
            ('(ab|cd)e', 'abcde', '0,1', ascii(('cde', 'cd'))),
            ('[abhgefdc]ij', 'hij', '0', ascii('hij')),
            ('^(ab|cd)e', 'abcde', '', ascii(None)),
            ('(abc|)ef', 'abcdef', '0,1', ascii(('ef', ''))),
            ('(a|b)c*d', 'abcd', '0,1', ascii(('bcd', 'b'))),

            ('(ab|ab*)bc', 'abc', '0,1', ascii(('abc', 'a'))),
            ('a([bc]*)c*', 'abc', '0,1', ascii(('abc', 'bc'))),
            ('a([bc]*)(c*d)', 'abcd', '0,1,2', ascii(('abcd', 'bc', 'd'))),
            ('a([bc]+)(c*d)', 'abcd', '0,1,2', ascii(('abcd', 'bc', 'd'))),
            ('a([bc]*)(c+d)', 'abcd', '0,1,2', ascii(('abcd', 'b', 'cd'))),
            ('a[bcd]*dcdcde', 'adcdcde', '0', ascii('adcdcde')),
            ('a[bcd]+dcdcde', 'adcdcde', '', ascii(None)),
            ('(ab|a)b*c', 'abc', '0,1', ascii(('abc', 'ab'))),
            ('((a)(b)c)(d)', 'abcd', '1,2,3,4', ascii(('abc', 'a', 'b', 'd'))),
            ('[a-zA-Z_][a-zA-Z0-9_]*', 'alpha', '0', ascii('alpha')),

            ('^a(bc+|b[eh])g|.h$', 'abh', '0,1', ascii(('bh', None))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'effgz', '0,1,2', ascii(('effgz',
              'effgz', None))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'ij', '0,1,2', ascii(('ij', 'ij',
              'j'))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'effg', '', ascii(None)),
            ('(bc+d$|ef*g.|h?i(j|k))', 'bcdd', '', ascii(None)),
            ('(bc+d$|ef*g.|h?i(j|k))', 'reffgz', '0,1,2', ascii(('effgz',
              'effgz', None))),
            ('(((((((((a)))))))))', 'a', '0', ascii('a')),
            ('multiple words of text', 'uh-uh', '', ascii(None)),
            ('multiple words', 'multiple words, yeah', '0',
              ascii('multiple words')),
            ('(.*)c(.*)', 'abcde', '0,1,2', ascii(('abcde', 'ab', 'de'))),

            ('\\((.*), (.*)\\)', '(a, b)', '2,1', ascii(('b', 'a'))),
            ('[k]', 'ab', '', ascii(None)),
            ('a[-]?c', 'ac', '0', ascii('ac')),
            ('(abc)\\1', 'abcabc', '1', ascii('abc')),
            ('([a-c]*)\\1', 'abcabc', '1', ascii('abc')),
            ('^(.+)?B', 'AB', '1', ascii('A')),
            ('(a+).\\1$', 'aaaaa', '0,1', ascii(('aaaaa', 'aa'))),
            ('^(a+).\\1$', 'aaaa', '', ascii(None)),
            ('(abc)\\1', 'abcabc', '0,1', ascii(('abcabc', 'abc'))),
            ('([a-c]+)\\1', 'abcabc', '0,1', ascii(('abcabc', 'abc'))),

            ('(a)\\1', 'aa', '0,1', ascii(('aa', 'a'))),
            ('(a+)\\1', 'aa', '0,1', ascii(('aa', 'a'))),
            ('(a+)+\\1', 'aa', '0,1', ascii(('aa', 'a'))),
            ('(a).+\\1', 'aba', '0,1', ascii(('aba', 'a'))),
            ('(a)ba*\\1', 'aba', '0,1', ascii(('aba', 'a'))),
            ('(aa|a)a\\1$', 'aaa', '0,1', ascii(('aaa', 'a'))),
            ('(a|aa)a\\1$', 'aaa', '0,1', ascii(('aaa', 'a'))),
            ('(a+)a\\1$', 'aaa', '0,1', ascii(('aaa', 'a'))),
            ('([abc]*)\\1', 'abcabc', '0,1', ascii(('abcabc', 'abc'))),
            ('(a)(b)c|ab', 'ab', '0,1,2', ascii(('ab', None, None))),

            ('(a)+x', 'aaax', '0,1', ascii(('aaax', 'a'))),
            ('([ac])+x', 'aacx', '0,1', ascii(('aacx', 'c'))),
            ('([^/]*/)*sub1/', 'd:msgs/tdir/sub1/trial/away.cpp', '0,1',
              ascii(('d:msgs/tdir/sub1/', 'tdir/'))),
            ('([^.]*)\\.([^:]*):[T ]+(.*)', 'track1.title:TBlah blah blah',
              '0,1,2,3', ascii(('track1.title:TBlah blah blah', 'track1',
              'title', 'Blah blah blah'))),
            ('([^N]*N)+', 'abNNxyzN', '0,1', ascii(('abNNxyzN', 'xyzN'))),
            ('([^N]*N)+', 'abNNxyz', '0,1', ascii(('abNN', 'N'))),
            ('([abc]*)x', 'abcx', '0,1', ascii(('abcx', 'abc'))),
            ('([abc]*)x', 'abc', '', ascii(None)),
            ('([xyz]*)x', 'abcx', '0,1', ascii(('x', ''))),
            ('(a)+b|aac', 'aac', '0,1', ascii(('aac', None))),

            # Test symbolic groups.
            ('(?P<i d>aaa)a', 'aaaa', '', regex.error, self.BAD_GROUP_NAME),
            ('(?P<id>aaa)a', 'aaaa', '0,id', ascii(('aaaa', 'aaa'))),
            ('(?P<id>aa)(?P=id)', 'aaaa', '0,id', ascii(('aaaa', 'aa'))),
            ('(?P<id>aa)(?P=xd)', 'aaaa', '', regex.error, self.UNKNOWN_GROUP),

            # Character properties.
            (r"\g", "g", '0', ascii('g')),
            (r"\g<1>", "g", '', regex.error, self.UNKNOWN_GROUP),
            (r"(.)\g<1>", "gg", '0', ascii('gg')),
            (r"(.)\g<1>", "gg", '', ascii(('gg', 'g'))),
            (r"\N", "N", '0', ascii('N')),
            (r"\N{LATIN SMALL LETTER A}", "a", '0', ascii('a')),
            (r"\p", "p", '0', ascii('p')),
            (r"\p{Ll}", "a", '0', ascii('a')),
            (r"\P", "P", '0', ascii('P')),
            (r"\P{Lu}", "p", '0', ascii('p')),

            # All tests from Perl.
            ('abc', 'abc', '0', ascii('abc')),
            ('abc', 'xbc', '', ascii(None)),
            ('abc', 'axc', '', ascii(None)),
            ('abc', 'abx', '', ascii(None)),
            ('abc', 'xabcy', '0', ascii('abc')),
            ('abc', 'ababc', '0', ascii('abc')),

            ('ab*c', 'abc', '0', ascii('abc')),
            ('ab*bc', 'abc', '0', ascii('abc')),
            ('ab*bc', 'abbc', '0', ascii('abbc')),
            ('ab*bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab{0,}bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab+bc', 'abbc', '0', ascii('abbc')),
            ('ab+bc', 'abc', '', ascii(None)),
            ('ab+bc', 'abq', '', ascii(None)),
            ('ab{1,}bc', 'abq', '', ascii(None)),
            ('ab+bc', 'abbbbc', '0', ascii('abbbbc')),

            ('ab{1,}bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab{1,3}bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab{3,4}bc', 'abbbbc', '0', ascii('abbbbc')),
            ('ab{4,5}bc', 'abbbbc', '', ascii(None)),
            ('ab?bc', 'abbc', '0', ascii('abbc')),
            ('ab?bc', 'abc', '0', ascii('abc')),
            ('ab{0,1}bc', 'abc', '0', ascii('abc')),
            ('ab?bc', 'abbbbc', '', ascii(None)),
            ('ab?c', 'abc', '0', ascii('abc')),
            ('ab{0,1}c', 'abc', '0', ascii('abc')),

            ('^abc$', 'abc', '0', ascii('abc')),
            ('^abc$', 'abcc', '', ascii(None)),
            ('^abc', 'abcc', '0', ascii('abc')),
            ('^abc$', 'aabc', '', ascii(None)),
            ('abc$', 'aabc', '0', ascii('abc')),
            ('^', 'abc', '0', ascii('')),
            ('$', 'abc', '0', ascii('')),
            ('a.c', 'abc', '0', ascii('abc')),
            ('a.c', 'axc', '0', ascii('axc')),
            ('a.*c', 'axyzc', '0', ascii('axyzc')),

            ('a.*c', 'axyzd', '', ascii(None)),
            ('a[bc]d', 'abc', '', ascii(None)),
            ('a[bc]d', 'abd', '0', ascii('abd')),
            ('a[b-d]e', 'abd', '', ascii(None)),
            ('a[b-d]e', 'ace', '0', ascii('ace')),
            ('a[b-d]', 'aac', '0', ascii('ac')),
            ('a[-b]', 'a-', '0', ascii('a-')),
            ('a[b-]', 'a-', '0', ascii('a-')),
            ('a[b-a]', '-', '', regex.error, self.BAD_CHAR_RANGE),
            ('a[]b', '-', '', regex.error, self.BAD_SET),

            ('a[', '-', '', regex.error, self.BAD_SET),
            ('a]', 'a]', '0', ascii('a]')),
            ('a[]]b', 'a]b', '0', ascii('a]b')),
            ('a[^bc]d', 'aed', '0', ascii('aed')),
            ('a[^bc]d', 'abd', '', ascii(None)),
            ('a[^-b]c', 'adc', '0', ascii('adc')),
            ('a[^-b]c', 'a-c', '', ascii(None)),
            ('a[^]b]c', 'a]c', '', ascii(None)),
            ('a[^]b]c', 'adc', '0', ascii('adc')),
            ('ab|cd', 'abc', '0', ascii('ab')),

            ('ab|cd', 'abcd', '0', ascii('ab')),
            ('()ef', 'def', '0,1', ascii(('ef', ''))),
            ('*a', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('(*)b', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('$b', 'b', '', ascii(None)),
            ('a\\', '-', '', regex.error, self.BAD_ESCAPE),
            ('a\\(b', 'a(b', '', ascii(('a(b',))),
            ('a\\(*b', 'ab', '0', ascii('ab')),
            ('a\\(*b', 'a((b', '0', ascii('a((b')),
            ('a\\\\b', 'a\\b', '0', ascii('a\\b')),

            ('abc)', '-', '', regex.error, self.TRAILING_CHARS),
            ('(abc', '-', '', regex.error, self.MISSING_RPAREN),
            ('((a))', 'abc', '0,1,2', ascii(('a', 'a', 'a'))),
            ('(a)b(c)', 'abc', '0,1,2', ascii(('abc', 'a', 'c'))),
            ('a+b+c', 'aabbabc', '0', ascii('abc')),
            ('a{1,}b{1,}c', 'aabbabc', '0', ascii('abc')),
            ('a**', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('a.+?c', 'abcabc', '0', ascii('abc')),
            ('(a+|b)*', 'ab', '0,1', ascii(('ab', 'b'))),
            ('(a+|b){0,}', 'ab', '0,1', ascii(('ab', 'b'))),

            ('(a+|b)+', 'ab', '0,1', ascii(('ab', 'b'))),
            ('(a+|b){1,}', 'ab', '0,1', ascii(('ab', 'b'))),
            ('(a+|b)?', 'ab', '0,1', ascii(('a', 'a'))),
            ('(a+|b){0,1}', 'ab', '0,1', ascii(('a', 'a'))),
            (')(', '-', '', regex.error, self.TRAILING_CHARS),
            ('[^ab]*', 'cde', '0', ascii('cde')),
            ('abc', '', '', ascii(None)),
            ('a*', '', '0', ascii('')),
            ('([abc])*d', 'abbbcd', '0,1', ascii(('abbbcd', 'c'))),
            ('([abc])*bcd', 'abcd', '0,1', ascii(('abcd', 'a'))),

            ('a|b|c|d|e', 'e', '0', ascii('e')),
            ('(a|b|c|d|e)f', 'ef', '0,1', ascii(('ef', 'e'))),
            ('abcd*efg', 'abcdefg', '0', ascii('abcdefg')),
            ('ab*', 'xabyabbbz', '0', ascii('ab')),
            ('ab*', 'xayabbbz', '0', ascii('a')),
            ('(ab|cd)e', 'abcde', '0,1', ascii(('cde', 'cd'))),
            ('[abhgefdc]ij', 'hij', '0', ascii('hij')),
            ('^(ab|cd)e', 'abcde', '', ascii(None)),
            ('(abc|)ef', 'abcdef', '0,1', ascii(('ef', ''))),
            ('(a|b)c*d', 'abcd', '0,1', ascii(('bcd', 'b'))),

            ('(ab|ab*)bc', 'abc', '0,1', ascii(('abc', 'a'))),
            ('a([bc]*)c*', 'abc', '0,1', ascii(('abc', 'bc'))),
            ('a([bc]*)(c*d)', 'abcd', '0,1,2', ascii(('abcd', 'bc', 'd'))),
            ('a([bc]+)(c*d)', 'abcd', '0,1,2', ascii(('abcd', 'bc', 'd'))),
            ('a([bc]*)(c+d)', 'abcd', '0,1,2', ascii(('abcd', 'b', 'cd'))),
            ('a[bcd]*dcdcde', 'adcdcde', '0', ascii('adcdcde')),
            ('a[bcd]+dcdcde', 'adcdcde', '', ascii(None)),
            ('(ab|a)b*c', 'abc', '0,1', ascii(('abc', 'ab'))),
            ('((a)(b)c)(d)', 'abcd', '1,2,3,4', ascii(('abc', 'a', 'b', 'd'))),
            ('[a-zA-Z_][a-zA-Z0-9_]*', 'alpha', '0', ascii('alpha')),

            ('^a(bc+|b[eh])g|.h$', 'abh', '0,1', ascii(('bh', None))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'effgz', '0,1,2', ascii(('effgz',
              'effgz', None))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'ij', '0,1,2', ascii(('ij', 'ij',
              'j'))),
            ('(bc+d$|ef*g.|h?i(j|k))', 'effg', '', ascii(None)),
            ('(bc+d$|ef*g.|h?i(j|k))', 'bcdd', '', ascii(None)),
            ('(bc+d$|ef*g.|h?i(j|k))', 'reffgz', '0,1,2', ascii(('effgz',
              'effgz', None))),
            ('((((((((((a))))))))))', 'a', '10', ascii('a')),
            ('((((((((((a))))))))))\\10', 'aa', '0', ascii('aa')),

            # Python does not have the same rules for \\41 so this is a syntax error
            #    ('((((((((((a))))))))))\\41', 'aa', '', ascii(None)),
            #    ('((((((((((a))))))))))\\41', 'a!', '0', ascii('a!')),
            ('((((((((((a))))))))))\\41', '', '', regex.error,
              self.UNKNOWN_GROUP),
            ('(?i)((((((((((a))))))))))\\41', '', '', regex.error,
              self.UNKNOWN_GROUP),

            ('(((((((((a)))))))))', 'a', '0', ascii('a')),
            ('multiple words of text', 'uh-uh', '', ascii(None)),
            ('multiple words', 'multiple words, yeah', '0',
              ascii('multiple words')),
            ('(.*)c(.*)', 'abcde', '0,1,2', ascii(('abcde', 'ab', 'de'))),
            ('\\((.*), (.*)\\)', '(a, b)', '2,1', ascii(('b', 'a'))),
            ('[k]', 'ab', '', ascii(None)),
            ('a[-]?c', 'ac', '0', ascii('ac')),
            ('(abc)\\1', 'abcabc', '1', ascii('abc')),
            ('([a-c]*)\\1', 'abcabc', '1', ascii('abc')),
            ('(?i)abc', 'ABC', '0', ascii('ABC')),

            ('(?i)abc', 'XBC', '', ascii(None)),
            ('(?i)abc', 'AXC', '', ascii(None)),
            ('(?i)abc', 'ABX', '', ascii(None)),
            ('(?i)abc', 'XABCY', '0', ascii('ABC')),
            ('(?i)abc', 'ABABC', '0', ascii('ABC')),
            ('(?i)ab*c', 'ABC', '0', ascii('ABC')),
            ('(?i)ab*bc', 'ABC', '0', ascii('ABC')),
            ('(?i)ab*bc', 'ABBC', '0', ascii('ABBC')),
            ('(?i)ab*?bc', 'ABBBBC', '0', ascii('ABBBBC')),
            ('(?i)ab{0,}?bc', 'ABBBBC', '0', ascii('ABBBBC')),

            ('(?i)ab+?bc', 'ABBC', '0', ascii('ABBC')),
            ('(?i)ab+bc', 'ABC', '', ascii(None)),
            ('(?i)ab+bc', 'ABQ', '', ascii(None)),
            ('(?i)ab{1,}bc', 'ABQ', '', ascii(None)),
            ('(?i)ab+bc', 'ABBBBC', '0', ascii('ABBBBC')),
            ('(?i)ab{1,}?bc', 'ABBBBC', '0', ascii('ABBBBC')),
            ('(?i)ab{1,3}?bc', 'ABBBBC', '0', ascii('ABBBBC')),
            ('(?i)ab{3,4}?bc', 'ABBBBC', '0', ascii('ABBBBC')),
            ('(?i)ab{4,5}?bc', 'ABBBBC', '', ascii(None)),
            ('(?i)ab??bc', 'ABBC', '0', ascii('ABBC')),

            ('(?i)ab??bc', 'ABC', '0', ascii('ABC')),
            ('(?i)ab{0,1}?bc', 'ABC', '0', ascii('ABC')),
            ('(?i)ab??bc', 'ABBBBC', '', ascii(None)),
            ('(?i)ab??c', 'ABC', '0', ascii('ABC')),
            ('(?i)ab{0,1}?c', 'ABC', '0', ascii('ABC')),
            ('(?i)^abc$', 'ABC', '0', ascii('ABC')),
            ('(?i)^abc$', 'ABCC', '', ascii(None)),
            ('(?i)^abc', 'ABCC', '0', ascii('ABC')),
            ('(?i)^abc$', 'AABC', '', ascii(None)),
            ('(?i)abc$', 'AABC', '0', ascii('ABC')),

            ('(?i)^', 'ABC', '0', ascii('')),
            ('(?i)$', 'ABC', '0', ascii('')),
            ('(?i)a.c', 'ABC', '0', ascii('ABC')),
            ('(?i)a.c', 'AXC', '0', ascii('AXC')),
            ('(?i)a.*?c', 'AXYZC', '0', ascii('AXYZC')),
            ('(?i)a.*c', 'AXYZD', '', ascii(None)),
            ('(?i)a[bc]d', 'ABC', '', ascii(None)),
            ('(?i)a[bc]d', 'ABD', '0', ascii('ABD')),
            ('(?i)a[b-d]e', 'ABD', '', ascii(None)),
            ('(?i)a[b-d]e', 'ACE', '0', ascii('ACE')),

            ('(?i)a[b-d]', 'AAC', '0', ascii('AC')),
            ('(?i)a[-b]', 'A-', '0', ascii('A-')),
            ('(?i)a[b-]', 'A-', '0', ascii('A-')),
            ('(?i)a[b-a]', '-', '', regex.error, self.BAD_CHAR_RANGE),
            ('(?i)a[]b', '-', '', regex.error, self.BAD_SET),
            ('(?i)a[', '-', '', regex.error, self.BAD_SET),
            ('(?i)a]', 'A]', '0', ascii('A]')),
            ('(?i)a[]]b', 'A]B', '0', ascii('A]B')),
            ('(?i)a[^bc]d', 'AED', '0', ascii('AED')),
            ('(?i)a[^bc]d', 'ABD', '', ascii(None)),

            ('(?i)a[^-b]c', 'ADC', '0', ascii('ADC')),
            ('(?i)a[^-b]c', 'A-C', '', ascii(None)),
            ('(?i)a[^]b]c', 'A]C', '', ascii(None)),
            ('(?i)a[^]b]c', 'ADC', '0', ascii('ADC')),
            ('(?i)ab|cd', 'ABC', '0', ascii('AB')),
            ('(?i)ab|cd', 'ABCD', '0', ascii('AB')),
            ('(?i)()ef', 'DEF', '0,1', ascii(('EF', ''))),
            ('(?i)*a', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('(?i)(*)b', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('(?i)$b', 'B', '', ascii(None)),

            ('(?i)a\\', '-', '', regex.error, self.BAD_ESCAPE),
            ('(?i)a\\(b', 'A(B', '', ascii(('A(B',))),
            ('(?i)a\\(*b', 'AB', '0', ascii('AB')),
            ('(?i)a\\(*b', 'A((B', '0', ascii('A((B')),
            ('(?i)a\\\\b', 'A\\B', '0', ascii('A\\B')),
            ('(?i)abc)', '-', '', regex.error, self.TRAILING_CHARS),
            ('(?i)(abc', '-', '', regex.error, self.MISSING_RPAREN),
            ('(?i)((a))', 'ABC', '0,1,2', ascii(('A', 'A', 'A'))),
            ('(?i)(a)b(c)', 'ABC', '0,1,2', ascii(('ABC', 'A', 'C'))),
            ('(?i)a+b+c', 'AABBABC', '0', ascii('ABC')),

            ('(?i)a{1,}b{1,}c', 'AABBABC', '0', ascii('ABC')),
            ('(?i)a**', '-', '', regex.error, self.NOTHING_TO_REPEAT),
            ('(?i)a.+?c', 'ABCABC', '0', ascii('ABC')),
            ('(?i)a.*?c', 'ABCABC', '0', ascii('ABC')),
            ('(?i)a.{0,5}?c', 'ABCABC', '0', ascii('ABC')),
            ('(?i)(a+|b)*', 'AB', '0,1', ascii(('AB', 'B'))),
            ('(?i)(a+|b){0,}', 'AB', '0,1', ascii(('AB', 'B'))),
            ('(?i)(a+|b)+', 'AB', '0,1', ascii(('AB', 'B'))),
            ('(?i)(a+|b){1,}', 'AB', '0,1', ascii(('AB', 'B'))),
            ('(?i)(a+|b)?', 'AB', '0,1', ascii(('A', 'A'))),

            ('(?i)(a+|b){0,1}', 'AB', '0,1', ascii(('A', 'A'))),
            ('(?i)(a+|b){0,1}?', 'AB', '0,1', ascii(('', None))),
            ('(?i))(', '-', '', regex.error, self.TRAILING_CHARS),
            ('(?i)[^ab]*', 'CDE', '0', ascii('CDE')),
            ('(?i)abc', '', '', ascii(None)),
            ('(?i)a*', '', '0', ascii('')),
            ('(?i)([abc])*d', 'ABBBCD', '0,1', ascii(('ABBBCD', 'C'))),
            ('(?i)([abc])*bcd', 'ABCD', '0,1', ascii(('ABCD', 'A'))),
            ('(?i)a|b|c|d|e', 'E', '0', ascii('E')),
            ('(?i)(a|b|c|d|e)f', 'EF', '0,1', ascii(('EF', 'E'))),

            ('(?i)abcd*efg', 'ABCDEFG', '0', ascii('ABCDEFG')),
            ('(?i)ab*', 'XABYABBBZ', '0', ascii('AB')),
            ('(?i)ab*', 'XAYABBBZ', '0', ascii('A')),
            ('(?i)(ab|cd)e', 'ABCDE', '0,1', ascii(('CDE', 'CD'))),
            ('(?i)[abhgefdc]ij', 'HIJ', '0', ascii('HIJ')),
            ('(?i)^(ab|cd)e', 'ABCDE', '', ascii(None)),
            ('(?i)(abc|)ef', 'ABCDEF', '0,1', ascii(('EF', ''))),
            ('(?i)(a|b)c*d', 'ABCD', '0,1', ascii(('BCD', 'B'))),
            ('(?i)(ab|ab*)bc', 'ABC', '0,1', ascii(('ABC', 'A'))),
            ('(?i)a([bc]*)c*', 'ABC', '0,1', ascii(('ABC', 'BC'))),

            ('(?i)a([bc]*)(c*d)', 'ABCD', '0,1,2', ascii(('ABCD', 'BC', 'D'))),
            ('(?i)a([bc]+)(c*d)', 'ABCD', '0,1,2', ascii(('ABCD', 'BC', 'D'))),
            ('(?i)a([bc]*)(c+d)', 'ABCD', '0,1,2', ascii(('ABCD', 'B', 'CD'))),
            ('(?i)a[bcd]*dcdcde', 'ADCDCDE', '0', ascii('ADCDCDE')),
            ('(?i)a[bcd]+dcdcde', 'ADCDCDE', '', ascii(None)),
            ('(?i)(ab|a)b*c', 'ABC', '0,1', ascii(('ABC', 'AB'))),
            ('(?i)((a)(b)c)(d)', 'ABCD', '1,2,3,4', ascii(('ABC', 'A', 'B',
              'D'))),
            ('(?i)[a-zA-Z_][a-zA-Z0-9_]*', 'ALPHA', '0', ascii('ALPHA')),
            ('(?i)^a(bc+|b[eh])g|.h$', 'ABH', '0,1', ascii(('BH', None))),
            ('(?i)(bc+d$|ef*g.|h?i(j|k))', 'EFFGZ', '0,1,2', ascii(('EFFGZ',
              'EFFGZ', None))),

            ('(?i)(bc+d$|ef*g.|h?i(j|k))', 'IJ', '0,1,2', ascii(('IJ', 'IJ',
              'J'))),
            ('(?i)(bc+d$|ef*g.|h?i(j|k))', 'EFFG', '', ascii(None)),
            ('(?i)(bc+d$|ef*g.|h?i(j|k))', 'BCDD', '', ascii(None)),
            ('(?i)(bc+d$|ef*g.|h?i(j|k))', 'REFFGZ', '0,1,2', ascii(('EFFGZ',
              'EFFGZ', None))),
            ('(?i)((((((((((a))))))))))', 'A', '10', ascii('A')),
            ('(?i)((((((((((a))))))))))\\10', 'AA', '0', ascii('AA')),
            #('(?i)((((((((((a))))))))))\\41', 'AA', '', ascii(None)),
            #('(?i)((((((((((a))))))))))\\41', 'A!', '0', ascii('A!')),
            ('(?i)(((((((((a)))))))))', 'A', '0', ascii('A')),
            ('(?i)(?:(?:(?:(?:(?:(?:(?:(?:(?:(a))))))))))', 'A', '1',
              ascii('A')),
            ('(?i)(?:(?:(?:(?:(?:(?:(?:(?:(?:(a|b|c))))))))))', 'C', '1',
              ascii('C')),
            ('(?i)multiple words of text', 'UH-UH', '', ascii(None)),

            ('(?i)multiple words', 'MULTIPLE WORDS, YEAH', '0',
             ascii('MULTIPLE WORDS')),
            ('(?i)(.*)c(.*)', 'ABCDE', '0,1,2', ascii(('ABCDE', 'AB', 'DE'))),
            ('(?i)\\((.*), (.*)\\)', '(A, B)', '2,1', ascii(('B', 'A'))),
            ('(?i)[k]', 'AB', '', ascii(None)),
        #    ('(?i)abcd', 'ABCD', SUCCEED, 'found+"-"+\\found+"-"+\\\\found', ascii(ABCD-$&-\\ABCD)),
        #    ('(?i)a(bc)d', 'ABCD', SUCCEED, 'g1+"-"+\\g1+"-"+\\\\g1', ascii(BC-$1-\\BC)),
            ('(?i)a[-]?c', 'AC', '0', ascii('AC')),
            ('(?i)(abc)\\1', 'ABCABC', '1', ascii('ABC')),
            ('(?i)([a-c]*)\\1', 'ABCABC', '1', ascii('ABC')),
            ('a(?!b).', 'abad', '0', ascii('ad')),
            ('a(?=d).', 'abad', '0', ascii('ad')),
            ('a(?=c|d).', 'abad', '0', ascii('ad')),

            ('a(?:b|c|d)(.)', 'ace', '1', ascii('e')),
            ('a(?:b|c|d)*(.)', 'ace', '1', ascii('e')),
            ('a(?:b|c|d)+?(.)', 'ace', '1', ascii('e')),
            ('a(?:b|(c|e){1,2}?|d)+?(.)', 'ace', '1,2', ascii(('c', 'e'))),

            # Lookbehind: split by : but not if it is escaped by -.
            ('(?<!-):(.*?)(?<!-):', 'a:bc-:de:f', '1', ascii('bc-:de')),
            # Escaping with \ as we know it.
            ('(?<!\\\):(.*?)(?<!\\\):', 'a:bc\\:de:f', '1', ascii('bc\\:de')),
            # Terminating with ' and escaping with ? as in edifact.
            ("(?<!\\?)'(.*?)(?<!\\?)'", "a'bc?'de'f", '1', ascii("bc?'de")),

            # Comments using the (?#...) syntax.

            ('w(?# comment', 'w', '', regex.error, self.MISSING_RPAREN),
            ('w(?# comment 1)xy(?# comment 2)z', 'wxyz', '0', ascii('wxyz')),

            # Check odd placement of embedded pattern modifiers.

            # Not an error under PCRE/PRE:
            # When the new behaviour is turned on positional inline flags affect
            # only what follows.
            ('w(?i)', 'W', '0', ascii('W')),
            ('w(?iV1)', 'W', '0', ascii(None)),
            ('w(?i)', 'w', '0', ascii('w')),
            ('w(?iV1)', 'w', '0', ascii('w')),
            ('(?i)w', 'W', '0', ascii('W')),
            ('(?iV1)w', 'W', '0', ascii('W')),

            # Comments using the x embedded pattern modifier.
            ("""(?x)w# comment 1
x y
# comment 2
z""", 'wxyz', '0', ascii('wxyz')),

            # Using the m embedded pattern modifier.
            ('^abc', """jkl
abc
xyz""", '', ascii(None)),
            ('(?m)^abc', """jkl
abc
xyz""", '0', ascii('abc')),

            ('(?m)abc$', """jkl
xyzabc
123""", '0', ascii('abc')),

            # Using the s embedded pattern modifier.
            ('a.b', 'a\nb', '', ascii(None)),
            ('(?s)a.b', 'a\nb', '0', ascii('a\nb')),

            # Test \w, etc. both inside and outside character classes.
            ('\\w+', '--ab_cd0123--', '0', ascii('ab_cd0123')),
            ('[\\w]+', '--ab_cd0123--', '0', ascii('ab_cd0123')),
            ('\\D+', '1234abc5678', '0', ascii('abc')),
            ('[\\D]+', '1234abc5678', '0', ascii('abc')),
            ('[\\da-fA-F]+', '123abc', '0', ascii('123abc')),
            # Not an error under PCRE/PRE:
            # ('[\\d-x]', '-', '', regex.error, self.SYNTAX_ERROR),
            (r'([\s]*)([\S]*)([\s]*)', ' testing!1972', '3,2,1', ascii(('',
              'testing!1972', ' '))),
            (r'(\s*)(\S*)(\s*)', ' testing!1972', '3,2,1', ascii(('',
              'testing!1972', ' '))),

            #
            # Post-1.5.2 additions.

            # xmllib problem.
            (r'(([a-z]+):)?([a-z]+)$', 'smil', '1,2,3', ascii((None, None,
              'smil'))),
            # Bug 110866: reference to undefined group.
            (r'((.)\1+)', '', '', regex.error, self.OPEN_GROUP),
            # Bug 111869: search (PRE/PCRE fails on this one, SRE doesn't).
            (r'.*d', 'abc\nabd', '0', ascii('abd')),
            # Bug 112468: various expected syntax errors.
            (r'(', '', '', regex.error, self.MISSING_RPAREN),
            (r'[\41]', '!', '0', ascii('!')),
            # Bug 114033: nothing to repeat.
            (r'(x?)?', 'x', '0', ascii('x')),
            # Bug 115040: rescan if flags are modified inside pattern.
            # If the new behaviour is turned on then positional inline flags
            # affect only what follows.
            (r' (?x)foo ', 'foo', '0', ascii('foo')),
            (r' (?V1x)foo ', 'foo', '0', ascii(None)),
            (r'(?x) foo ', 'foo', '0', ascii('foo')),
            (r'(?V1x) foo ', 'foo', '0', ascii('foo')),
            (r'(?x)foo ', 'foo', '0', ascii('foo')),
            (r'(?V1x)foo ', 'foo', '0', ascii('foo')),
            # Bug 115618: negative lookahead.
            (r'(?<!abc)(d.f)', 'abcdefdof', '0', ascii('dof')),
            # Bug 116251: character class bug.
            (r'[\w-]+', 'laser_beam', '0', ascii('laser_beam')),
            # Bug 123769+127259: non-greedy backtracking bug.
            (r'.*?\S *:', 'xx:', '0', ascii('xx:')),
            (r'a[ ]*?\ (\d+).*', 'a   10', '0', ascii('a   10')),
            (r'a[ ]*?\ (\d+).*', 'a    10', '0', ascii('a    10')),
            # Bug 127259: \Z shouldn't depend on multiline mode.
            (r'(?ms).*?x\s*\Z(.*)','xx\nx\n', '1', ascii('')),
            # Bug 128899: uppercase literals under the ignorecase flag.
            (r'(?i)M+', 'MMM', '0', ascii('MMM')),
            (r'(?i)m+', 'MMM', '0', ascii('MMM')),
            (r'(?i)[M]+', 'MMM', '0', ascii('MMM')),
            (r'(?i)[m]+', 'MMM', '0', ascii('MMM')),
            # Bug 130748: ^* should be an error (nothing to repeat).
            # In 'regex' we won't bother to complain about this.
            # (r'^*', '', '', regex.error, self.NOTHING_TO_REPEAT),
            # Bug 133283: minimizing repeat problem.
            (r'"(?:\\"|[^"])*?"', r'"\""', '0', ascii(r'"\""')),
            # Bug 477728: minimizing repeat problem.
            (r'^.*?$', 'one\ntwo\nthree\n', '', ascii(None)),
            # Bug 483789: minimizing repeat problem.
            (r'a[^>]*?b', 'a>b', '', ascii(None)),
            # Bug 490573: minimizing repeat problem.
            (r'^a*?$', 'foo', '', ascii(None)),
            # Bug 470582: nested groups problem.
            (r'^((a)c)?(ab)$', 'ab', '1,2,3', ascii((None, None, 'ab'))),
            # Another minimizing repeat problem (capturing groups in assertions).
            ('^([ab]*?)(?=(b)?)c', 'abc', '1,2', ascii(('ab', None))),
            ('^([ab]*?)(?!(b))c', 'abc', '1,2', ascii(('ab', None))),
            ('^([ab]*?)(?<!(a))c', 'abc', '1,2', ascii(('ab', None))),
            # Bug 410271: \b broken under locales.
            (r'\b.\b', 'a', '0', ascii('a')),
            (r'\b.\b', '\N{LATIN CAPITAL LETTER A WITH DIAERESIS}', '0',
              ascii('\xc4')),
            (r'\w', '\N{LATIN CAPITAL LETTER A WITH DIAERESIS}', '0',
              ascii('\xc4')),
        ]

        for t in tests:
            excval = None
            try:
                if len(t) == 4:
                    pattern, string, groups, expected = t
                else:
                    pattern, string, groups, expected, excval = t
            except ValueError:
                fields = ", ".join([ascii(f) for f in t[ : 3]] + ["..."])
                self.fail("Incorrect number of test fields: ({})".format(fields))
            else:
                group_list = []
                if groups:
                    for group in groups.split(","):
                        try:
                            group_list.append(int(group))
                        except ValueError:
                            group_list.append(group)

                if excval is not None:
                    self.assertRaisesRegex(expected, excval,
                                           regex.search, pattern, string)
                else:
                    m = regex.search(pattern, string)
                    if m:
                        if group_list:
                            actual = ascii(m.group(*group_list))
                        else:
                            actual = ascii(m[:])
                    else:
                        actual = ascii(m)

                    self.assertEqual(actual, expected)

    def test_replacement(self):
        self.assertEquals(regex.sub("test\?", "result\?\.\a\q\m\n", "test?"),
          "result\?\.\a\q\m\n")
        self.assertEquals(regex.sub(r"test\?", "result\?\.\a\q\m\n", "test?"),
          "result\?\.\a\q\m\n")

        self.assertEquals(regex.sub('(.)', r"\1\1", 'x'), 'xx')
        self.assertEquals(regex.sub('(.)', regex.escape(r"\1\1"), 'x'),
          r"\1\1")
        self.assertEquals(regex.sub('(.)', r"\\1\\1", 'x'), r"\1\1")
        self.assertEquals(regex.sub('(.)', lambda m: r"\1\1", 'x'), r"\1\1")

    def test_common_prefix(self):
        # Very long common prefix
        all = string.ascii_lowercase + string.digits + string.ascii_uppercase
        side = all * 4
        regexp = '(' + side + '|' + side + ')'
        self.assertEquals(repr(type(regex.compile(regexp))),
          self.PATTERN_CLASS)

    def test_captures(self):
        self.assertEquals(regex.search(r"(\w)+", "abc").captures(1), ['a', 'b',
          'c'])
        self.assertEquals(regex.search(r"(\w{3})+", "abcdef").captures(0, 1),
          (['abcdef'], ['abc', 'def']))
        self.assertEquals(regex.search(r"^(\d{1,3})(?:\.(\d{1,3})){3}$",
          "192.168.0.1").captures(1, 2), (['192', ], ['168', '0', '1']))
        self.assertEquals(regex.match(r"^([0-9A-F]{2}){4} ([a-z]\d){5}$",
          "3FB52A0C a2c4g3k9d3").captures(1, 2), (['3F', 'B5', '2A', '0C'],
          ['a2', 'c4', 'g3', 'k9', 'd3']))
        self.assertEquals(regex.match("([a-z]W)([a-z]X)+([a-z]Y)",
          "aWbXcXdXeXfY").captures(1, 2, 3), (['aW'], ['bX', 'cX', 'dX', 'eX'],
          ['fY']))

        self.assertEquals(regex.search(r".*?(?=(.)+)b", "ab").captures(1),
          ['b'])
        self.assertEquals(regex.search(r".*?(?>(.){0,2})d",
          "abcd").captures(1), ['b', 'c'])
        self.assertEquals(regex.search(r"(.)+", "a").captures(1), ['a'])

    def test_guards(self):
        m = regex.search(r"(X.*?Y\s*){3}(X\s*)+AB:",
          "XY\nX Y\nX  Y\nXY\nXX AB:")
        self.assertEquals(m.span(0, 1, 2), ((3, 21), (12, 15), (16, 18)))

        m = regex.search(r"(X.*?Y\s*){3,}(X\s*)+AB:",
          "XY\nX Y\nX  Y\nXY\nXX AB:")
        self.assertEquals(m.span(0, 1, 2), ((0, 21), (12, 15), (16, 18)))

        m = regex.search(r'\d{4}(\s*\w)?\W*((?!\d)\w){2}', "9999XX")
        self.assertEquals(m.span(0, 1, 2), ((0, 6), (-1, -1), (5, 6)))

        m = regex.search(r'A\s*?.*?(\n+.*?\s*?){0,2}\(X', 'A\n1\nS\n1 (X')
        self.assertEquals(m.span(0, 1), ((0, 10), (5, 8)))

        m = regex.search('Derde\s*:', 'aaaaaa:\nDerde:')
        self.assertEquals(m.span(), (8, 14))
        m = regex.search('Derde\s*:', 'aaaaa:\nDerde:')
        self.assertEquals(m.span(), (7, 13))

    def test_turkic(self):
        # Turkish has dotted and dotless I/i.
        pairs = "I=i;I=\u0131;i=\u0130"

        all_chars = set()
        matching = set()
        for pair in pairs.split(";"):
            ch1, ch2 = pair.split("=")
            all_chars.update((ch1, ch2))
            matching.add((ch1, ch1))
            matching.add((ch1, ch2))
            matching.add((ch2, ch1))
            matching.add((ch2, ch2))

        for ch1 in all_chars:
            for ch2 in all_chars:
                m = regex.match(r"(?i)\A" + ch1 + r"\Z", ch2)
                if m:
                    if (ch1, ch2) not in matching:
                        self.fail("{} matching {}".format(ascii(ch1),
                          ascii(ch2)))
                else:
                    if (ch1, ch2) in matching:
                        self.fail("{} not matching {}".format(ascii(ch1),
                          ascii(ch2)))

    def test_named_lists(self):
        options = ["one", "two", "three"]
        self.assertEquals(regex.match(r"333\L<bar>444", "333one444",
          bar=options).group(), "333one444")
        self.assertEquals(regex.match(r"(?i)333\L<bar>444", "333TWO444",
          bar=options).group(), "333TWO444")
        self.assertEquals(regex.match(r"333\L<bar>444", "333four444",
          bar=options), None)

        options = [b"one", b"two", b"three"]
        self.assertEquals(regex.match(br"333\L<bar>444", b"333one444",
          bar=options).group(), b"333one444")
        self.assertEquals(regex.match(br"(?i)333\L<bar>444", b"333TWO444",
          bar=options).group(), b"333TWO444")
        self.assertEquals(regex.match(br"333\L<bar>444", b"333four444",
          bar=options), None)

        self.assertEquals(repr(type(regex.compile(r"3\L<bar>4\L<bar>+5",
          bar=["one", "two", "three"]))), self.PATTERN_CLASS)

        self.assertEquals(regex.findall(r"^\L<options>", "solid QWERT",
          options=set(['good', 'brilliant', '+s\\ol[i}d'])), [])
        self.assertEquals(regex.findall(r"^\L<options>", "+solid QWERT",
          options=set(['good', 'brilliant', '+solid'])), ['+solid'])

        options = ["STRASSE"]
        self.assertEquals(regex.match(r"(?fi)\L<words>",
          "stra\N{LATIN SMALL LETTER SHARP S}e", words=options).span(), (0, 6))

        options = ["STRASSE", "stress"]
        self.assertEquals(regex.match(r"(?fi)\L<words>",
          "stra\N{LATIN SMALL LETTER SHARP S}e", words=options).span(), (0, 6))

        options = ["stra\N{LATIN SMALL LETTER SHARP S}e"]
        self.assertEquals(regex.match(r"(?fi)\L<words>", "STRASSE",
          words=options).span(), (0, 7))

        options = ["kit"]
        self.assertEquals(regex.search(r"(?i)\L<words>",
          "SKITS", words=options).span(), (1, 4))
        self.assertEquals(regex.search(r"(?i)\L<words>",
          "SK\N{LATIN CAPITAL LETTER I WITH DOT ABOVE}TS",
          words=options).span(), (1, 4))

        self.assertEquals(regex.search(r"(?fi)\b(\w+) +\1\b",
          " stra\N{LATIN SMALL LETTER SHARP S}e STRASSE ").span(), (1, 15))
        self.assertEquals(regex.search(r"(?fi)\b(\w+) +\1\b",
          " STRASSE stra\N{LATIN SMALL LETTER SHARP S}e ").span(), (1, 15))

        self.assertEquals(regex.search(r"^\L<options>$", "",
          options=[]).span(), (0, 0))

    def test_fuzzy(self):
        # Some tests borrowed from TRE library tests.
        self.assertEquals(repr(type(regex.compile('(fou){s,e<=1}'))),
          self.PATTERN_CLASS)
        self.assertEquals(repr(type(regex.compile('(fuu){s}'))),
          self.PATTERN_CLASS)
        self.assertEquals(repr(type(regex.compile('(fuu){s,e}'))),
          self.PATTERN_CLASS)
        self.assertEquals(repr(type(regex.compile('(anaconda){1i+1d<1,s<=1}'))),
          self.PATTERN_CLASS)
        self.assertEquals(repr(type(regex.compile('(anaconda){1i+1d<1,s<=1,e<=10}'))),
          self.PATTERN_CLASS)
        self.assertEquals(repr(type(regex.compile('(anaconda){s<=1,e<=1,1i+1d<1}'))),
          self.PATTERN_CLASS)

        text = 'molasses anaconda foo bar baz smith anderson '
        self.assertEquals(regex.search('(znacnda){s<=1,e<=3,1i+1d<1}', text),
          None)
        self.assertEquals(regex.search('(znacnda){s<=1,e<=3,1i+1d<2}',
          text).span(0, 1), ((9, 17), (9, 17)))
        self.assertEquals(regex.search('(ananda){1i+1d<2}', text), None)
        self.assertEquals(regex.search(r"(?:\bznacnda){e<=2}", text)[0],
          "anaconda")
        self.assertEquals(regex.search(r"(?:\bnacnda){e<=2}", text)[0],
          "anaconda")

        text = 'anaconda foo bar baz smith anderson'
        self.assertEquals(regex.search('(fuu){i<=3,d<=3,e<=5}', text).span(0,
          1), ((0, 0), (0, 0)))
        self.assertEquals(regex.search('(?b)(fuu){i<=3,d<=3,e<=5}',
          text).span(0, 1), ((9, 10), (9, 10)))
        self.assertEquals(regex.search('(fuu){i<=2,d<=2,e<=5}', text).span(0,
          1), ((7, 10), (7, 10)))
        self.assertEquals(regex.search('(?e)(fuu){i<=2,d<=2,e<=5}',
          text).span(0, 1), ((9, 10), (9, 10)))
        self.assertEquals(regex.search('(fuu){i<=3,d<=3,e}', text).span(0, 1),
          ((0, 0), (0, 0)))
        self.assertEquals(regex.search('(?b)(fuu){i<=3,d<=3,e}', text).span(0,
          1), ((9, 10), (9, 10)))

        self.assertEquals(repr(type(regex.compile('(approximate){s<=3,1i+1d<3}'))),
          self.PATTERN_CLASS)

        # No cost limit.
        self.assertEquals(regex.search('(foobar){e}',
          'xirefoabralfobarxie').span(0, 1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('(?e)(foobar){e}',
          'xirefoabralfobarxie').span(0, 1), ((0, 3), (0, 3)))
        self.assertEquals(regex.search('(?b)(foobar){e}',
          'xirefoabralfobarxie').span(0, 1), ((11, 16), (11, 16)))

        # At most two errors.
        self.assertEquals(regex.search('(foobar){e<=2}',
          'xirefoabrzlfd').span(0, 1), ((4, 9), (4, 9)))
        self.assertEquals(regex.search('(foobar){e<=2}', 'xirefoabzlfd'), None)

        # At most two inserts or substitutions and max two errors total.
        self.assertEquals(regex.search('(foobar){i<=2,s<=2,e<=2}',
          'oobargoobaploowap').span(0, 1), ((5, 11), (5, 11)))

        # Find best whole word match for "foobar".
        self.assertEquals(regex.search('\\b(foobar){e}\\b', 'zfoobarz').span(0,
          1), ((0, 8), (0, 8)))
        self.assertEquals(regex.search('\\b(foobar){e}\\b',
          'boing zfoobarz goobar woop').span(0, 1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('(?b)\\b(foobar){e}\\b',
          'boing zfoobarz goobar woop').span(0, 1), ((15, 21), (15, 21)))

        # Match whole string, allow only 1 error.
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foobar').span(0,
          1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'xfoobar').span(0,
          1), ((0, 7), (0, 7)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foobarx').span(0,
          1), ((0, 7), (0, 7)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'fooxbar').span(0,
          1), ((0, 7), (0, 7)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foxbar').span(0,
          1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'xoobar').span(0,
          1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foobax').span(0,
          1), ((0, 6), (0, 6)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'oobar').span(0, 1),
          ((0, 5), (0, 5)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'fobar').span(0, 1),
          ((0, 5), (0, 5)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'fooba').span(0, 1),
          ((0, 5), (0, 5)))
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'xfoobarx'), None)
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foobarxx'), None)
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'xxfoobar'), None)
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'xfoxbar'), None)
        self.assertEquals(regex.search('^(foobar){e<=1}$', 'foxbarx'), None)

        # At most one insert, two deletes, and three substitutions.
        # Additionally, deletes cost two and substitutes one, and total
        # cost must be less than 4.
        self.assertEquals(regex.search('(foobar){i<=1,d<=2,s<=3,2d+1s<4}',
          '3oifaowefbaoraofuiebofasebfaobfaorfeoaro').span(0, 1), ((6, 13), (6,
          13)))
        self.assertEquals(regex.search('(?b)(foobar){i<=1,d<=2,s<=3,2d+1s<4}',
          '3oifaowefbaoraofuiebofasebfaobfaorfeoaro').span(0, 1), ((26, 33),
          (26, 33)))

        # Partially fuzzy matches.
        self.assertEquals(regex.search('foo(bar){e<=1}zap',
          'foobarzap').span(0, 1), ((0, 9), (3, 6)))
        self.assertEquals(regex.search('foo(bar){e<=1}zap', 'fobarzap'), None)
        self.assertEquals(regex.search('foo(bar){e<=1}zap', 'foobrzap').span(0,
          1), ((0, 8), (3, 5)))

        text = ('www.cnn.com 64.236.16.20\nwww.slashdot.org 66.35.250.150\n'
          'For useful information, use www.slashdot.org\nthis is demo data!\n')
        self.assertEquals(regex.search(r'(?s)^.*(dot.org){e}.*$', text).span(0,
          1), ((0, 120), (120, 120)))
        self.assertEquals(regex.search(r'(?es)^.*(dot.org){e}.*$',
          text).span(0, 1), ((0, 120), (93, 100)))
        self.assertEquals(regex.search(r'^.*(dot.org){e}.*$', text).span(0, 1),
          ((0, 119), (24, 101)))

        # Behaviour is unexpected, but arguably not wrong. It first finds the
        # best match, then the best in what follows, etc.
        self.assertEquals(regex.findall(r"\b\L<words>{e<=1}\b",
          " book cot dog desk ", words="cat dog".split()), ["cot", "dog"])
        self.assertEquals(regex.findall(r"\b\L<words>{e<=1}\b",
          " book dog cot desk ", words="cat dog".split()), [" dog", "cot"])
        self.assertEquals(regex.findall(r"(?e)\b\L<words>{e<=1}\b",
          " book dog cot desk ", words="cat dog".split()), ["dog", "cot"])
        self.assertEquals(regex.findall(r"(?r)\b\L<words>{e<=1}\b",
          " book cot dog desk ", words="cat dog".split()), ["dog ", "cot"])
        self.assertEquals(regex.findall(r"(?er)\b\L<words>{e<=1}\b",
          " book cot dog desk ", words="cat dog".split()), ["dog", "cot"])
        self.assertEquals(regex.findall(r"(?r)\b\L<words>{e<=1}\b",
          " book dog cot desk ", words="cat dog".split()), ["cot", "dog"])
        self.assertEquals(regex.findall(br"\b\L<words>{e<=1}\b",
          b" book cot dog desk ", words=b"cat dog".split()), [b"cot", b"dog"])
        self.assertEquals(regex.findall(br"\b\L<words>{e<=1}\b",
          b" book dog cot desk ", words=b"cat dog".split()), [b" dog", b"cot"])
        self.assertEquals(regex.findall(br"(?e)\b\L<words>{e<=1}\b",
          b" book dog cot desk ", words=b"cat dog".split()), [b"dog", b"cot"])
        self.assertEquals(regex.findall(br"(?r)\b\L<words>{e<=1}\b",
          b" book cot dog desk ", words=b"cat dog".split()), [b"dog ", b"cot"])
        self.assertEquals(regex.findall(br"(?er)\b\L<words>{e<=1}\b",
          b" book cot dog desk ", words=b"cat dog".split()), [b"dog", b"cot"])
        self.assertEquals(regex.findall(br"(?r)\b\L<words>{e<=1}\b",
          b" book dog cot desk ", words=b"cat dog".split()), [b"cot", b"dog"])

        self.assertEquals(regex.search(r"(\w+) (\1{e<=1})",
          "foo fou").groups(), ("foo", "fou"))
        self.assertEquals(regex.search(r"(?r)(\2{e<=1}) (\w+)",
          "foo fou").groups(), ("foo", "fou"))
        self.assertEquals(regex.search(br"(\w+) (\1{e<=1})",
          b"foo fou").groups(), (b"foo", b"fou"))

        self.assertEquals(regex.findall(r"(?:(?:QR)+){e}","abcde"), ["abcde",
          ""])
        self.assertEquals(regex.findall(r"(?:Q+){e}","abc"), ["abc", ""])

        # Hg issue 41
        self.assertEquals(regex.match(r"(?:service detection){0<e<5}",
          "servic detection").span(), (0, 16))
        self.assertEquals(regex.match(r"(?:service detection){0<e<5}",
          "service detect").span(), (0, 14))
        self.assertEquals(regex.match(r"(?:service detection){0<e<5}",
          "service detecti").span(), (0, 15))
        self.assertEquals(regex.match(r"(?:service detection){0<e<5}",
          "service detection"), None)
        self.assertEquals(regex.match(r"(?:service detection){0<e<5}",
          "in service detection").span(), (0, 20))

    def test_recursive(self):
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "xx")[ : ],
          ("xx", "x", ""))
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "aba")[ : ],
          ("aba", "a", "b"))
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "abba")[ : ],
          ("abba", "a", None))
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "kayak")[ : ],
          ("kayak", "k", None))
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "paper")[ : ],
          ("pap", "p", "a"))
        self.assertEquals(regex.search(r"(\w)(?:(?R)|(\w?))\1", "dontmatchme"),
          None)

        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)", "xx")[ : ],
          ("xx", "", "x"))
        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)", "aba")[ :
          ], ("aba", "b", "a"))
        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)", "abba")[ :
          ], ("abba", None, "a"))
        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)", "kayak")[ :
          ], ("kayak", None, "k"))
        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)", "paper")[ :
          ], ("pap", "a", "p"))
        self.assertEquals(regex.search(r"(?r)\2(?:(\w?)|(?R))(\w)",
          "dontmatchme"), None)

        self.assertEquals(regex.search(r"\(((?>[^()]+)|(?R))*\)",
          "(ab(cd)ef)")[ : ], ("(ab(cd)ef)", "ef"))
        self.assertEquals(regex.search(r"\(((?>[^()]+)|(?R))*\)",
          "(ab(cd)ef)").captures(1), ["ab", "cd", "(cd)", "ef"])

        self.assertEquals(regex.search(r"(?r)\(((?R)|(?>[^()]+))*\)",
          "(ab(cd)ef)")[ : ], ("(ab(cd)ef)", "ab"))
        self.assertEquals(regex.search(r"(?r)\(((?R)|(?>[^()]+))*\)",
          "(ab(cd)ef)").captures(1), ["ef", "cd", "(cd)", "ab"])

        self.assertEquals(regex.search(r"\(([^()]+|(?R))*\)",
          "some text (a(b(c)d)e) more text")[ : ], ("(a(b(c)d)e)",  "e"))

        self.assertEquals(regex.search(r"(?r)\(((?R)|[^()]+)*\)",
          "some text (a(b(c)d)e) more text")[ : ], ("(a(b(c)d)e)",  "a"))

        self.assertEquals(regex.search(r"(foo(\(((?:(?>[^()]+)|(?2))*)\)))",
          "foo(bar(baz)+baz(bop))")[ : ], ("foo(bar(baz)+baz(bop))",
          "foo(bar(baz)+baz(bop))", "(bar(baz)+baz(bop))",
          "bar(baz)+baz(bop)"))

        self.assertEquals(regex.search(r"(?r)(foo(\(((?:(?2)|(?>[^()]+))*)\)))",
          "foo(bar(baz)+baz(bop))")[ : ], ("foo(bar(baz)+baz(bop))",
          "foo(bar(baz)+baz(bop))", "(bar(baz)+baz(bop))",
          "bar(baz)+baz(bop)"))

        rgx = regex.compile(r"""^\s*(<\s*([a-zA-Z:]+)(?:\s*[a-zA-Z:]*\s*=\s*(?:'[^']*'|"[^"]*"))*\s*(/\s*)?>(?:[^<>]*|(?1))*(?(3)|<\s*/\s*\2\s*>))\s*$""")
        self.assertEquals(bool(rgx.search('<foo><bar></bar></foo>')), True)
        self.assertEquals(bool(rgx.search('<foo><bar></foo></bar>')), False)
        self.assertEquals(bool(rgx.search('<foo><bar/></foo>')), True)
        self.assertEquals(bool(rgx.search('<foo><bar></foo>')), False)
        self.assertEquals(bool(rgx.search('<foo bar=baz/>')), False)

        self.assertEquals(bool(rgx.search('<foo bar="baz">')), False)
        self.assertEquals(bool(rgx.search('<foo bar="baz"/>')), True)
        self.assertEquals(bool(rgx.search('<    fooo   /  >')), True)
        # The next regex should and does match. Perl 5.14 agrees.
        #self.assertEquals(bool(rgx.search('<foo/>foo')), False)
        self.assertEquals(bool(rgx.search('foo<foo/>')), False)

        self.assertEquals(bool(rgx.search('<foo>foo</foo>')), True)
        self.assertEquals(bool(rgx.search('<foo><bar/>foo</foo>')), True)
        self.assertEquals(bool(rgx.search('<a><b><c></c></b></a>')), True)

    def test_copy(self):
        # PatternObjects are immutable, therefore there's no need to clone them.
        r = regex.compile("a")
        self.assert_(copy.copy(r) is r)
        self.assert_(copy.deepcopy(r) is r)

        # MatchObjects are normally mutable because the target string can be
        # detached. However, after the target string has been detached, a
        # MatchObject becomes immutable, so there's no need to clone it.
        m = r.match("a")
        self.assert_(copy.copy(m) is not m)
        self.assert_(copy.deepcopy(m) is not m)

        self.assert_(m.string is not None)
        m2 = copy.copy(m)
        m2.detach_string()
        self.assert_(m.string is not None)
        self.assert_(m2.string is None)

        # The following behaviour matches that of the re module.
        it = regex.finditer(".", "ab")
        it2 = copy.copy(it)
        self.assertEquals(next(it).group(), "a")
        self.assertEquals(next(it2).group(), "b")

        # The following behaviour matches that of the re module.
        it = regex.finditer(".", "ab")
        it2 = copy.deepcopy(it)
        self.assertEquals(next(it).group(), "a")
        self.assertEquals(next(it2).group(), "b")

        # The following behaviour is designed to match that of copying 'finditer'.
        it = regex.splititer(" ", "a b")
        it2 = copy.copy(it)
        self.assertEquals(next(it), "a")
        self.assertEquals(next(it2), "b")

        # The following behaviour is designed to match that of copying 'finditer'.
        it = regex.splititer(" ", "a b")
        it2 = copy.deepcopy(it)
        self.assertEquals(next(it), "a")
        self.assertEquals(next(it2), "b")

    def test_format(self):
        self.assertEquals(regex.subf(r"(\w+) (\w+)", "{0} => {2} {1}",
          "foo bar"), "foo bar => bar foo")
        self.assertEquals(regex.subf(r"(?<word1>\w+) (?<word2>\w+)",
          "{word2} {word1}", "foo bar"), "bar foo")

        self.assertEquals(regex.subfn(r"(\w+) (\w+)", "{0} => {2} {1}",
          "foo bar"), ("foo bar => bar foo", 1))
        self.assertEquals(regex.subfn(r"(?<word1>\w+) (?<word2>\w+)",
          "{word2} {word1}", "foo bar"), ("bar foo", 1))

        self.assertEquals(regex.match(r"(\w+) (\w+)",
          "foo bar").expandf("{0} => {2} {1}"), "foo bar => bar foo")

    def test_fullmatch(self):
        self.assertEquals(bool(regex.fullmatch(r"abc", "abc")), True)
        self.assertEquals(bool(regex.fullmatch(r"abc", "abcx")), False)
        self.assertEquals(bool(regex.fullmatch(r"abc", "abcx", endpos=3)),
          True)

        self.assertEquals(bool(regex.fullmatch(r"abc", "xabc", pos=1)), True)
        self.assertEquals(bool(regex.fullmatch(r"abc", "xabcy", pos=1)), False)
        self.assertEquals(bool(regex.fullmatch(r"abc", "xabcy", pos=1,
          endpos=4)), True)

        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "abc")), True)
        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "abcx")), False)
        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "abcx", endpos=3)),
          True)

        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "xabc", pos=1)),
          True)
        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "xabcy", pos=1)),
          False)
        self.assertEquals(bool(regex.fullmatch(r"(?r)abc", "xabcy", pos=1,
          endpos=4)), True)

    def test_hg_bugs(self):
        # Hg issue 28
        self.assertEquals(bool(regex.compile("(?>b)", flags=regex.V1)), True)

        # Hg issue 29
        self.assertEquals(bool(regex.compile("^((?>\w+)|(?>\s+))*$",
          flags=regex.V1)), True)

        # Hg issue 31
        self.assertEquals(regex.findall(r"\((?:(?>[^()]+)|(?R))*\)",
          "a(bcd(e)f)g(h)"), ['(bcd(e)f)', '(h)'])
        self.assertEquals(regex.findall(r"\((?:(?:[^()]+)|(?R))*\)",
          "a(bcd(e)f)g(h)"), ['(bcd(e)f)', '(h)'])
        self.assertEquals(regex.findall(r"\((?:(?>[^()]+)|(?R))*\)",
          "a(b(cd)e)f)g)h"), ['(b(cd)e)'])
        self.assertEquals(regex.findall(r"\((?:(?>[^()]+)|(?R))*\)",
          "a(bc(d(e)f)gh"), ['(d(e)f)'])
        self.assertEquals(regex.findall(r"(?r)\((?:(?>[^()]+)|(?R))*\)",
          "a(bc(d(e)f)gh"), ['(d(e)f)'])
        self.assertEquals([m.group() for m in
          regex.finditer(r"\((?:[^()]*+|(?0))*\)", "a(b(c(de)fg)h")],
          ['(c(de)fg)'])

        # Hg issue 32
        self.assertEquals(regex.search("a(bc)d", "abcd", regex.I |
          regex.V1).group(0), "abcd")

        # Hg issue 33
        self.assertEquals(regex.search("([\da-f:]+)$", "E", regex.I |
          regex.V1).group(0), "E")
        self.assertEquals(regex.search("([\da-f:]+)$", "e", regex.I |
          regex.V1).group(0), "e")

        # Hg issue 34
        self.assertEquals(regex.search("^(?=ab(de))(abd)(e)", "abde").groups(),
          ('de', 'abd', 'e'))

        # Hg issue 35
        self.assertEquals(bool(regex.match(r"\ ", " ", flags=regex.X)), True)

        # Hg issue 36
        self.assertEquals(regex.search(r"^(a|)\1{2}b", "b").group(0, 1), ('b',
          ''))

        # Hg issue 37
        self.assertEquals(regex.search("^(a){0,0}", "abc").group(0, 1), ('',
          None))

        # Hg issue 38
        self.assertEquals(regex.search("(?>.*/)b", "a/b").group(0), "a/b")

        # Hg issue 39
        self.assertEquals(regex.search(r"(?V0)((?i)blah)\s+\1",
          "blah BLAH").group(0, 1), ("blah BLAH", "blah"))
        self.assertEquals(regex.search(r"(?V1)((?i)blah)\s+\1", "blah BLAH"),
          None)

        # Hg issue 40
        self.assertEquals(regex.search(r"(\()?[^()]+(?(1)\)|)",
          "(abcd").group(0), "abcd")

        # Hg issue 42
        self.assertEquals(regex.search("(a*)*", "a").span(1), (1, 1))
        self.assertEquals(regex.search("(a*)*", "aa").span(1), (2, 2))
        self.assertEquals(regex.search("(a*)*", "aaa").span(1), (3, 3))

        # Hg issue 43
        self.assertEquals(regex.search("a(?#xxx)*", "aaa").group(), "aaa")

        # Hg issue 44
        self.assertEquals(regex.search("(?=abc){3}abc", "abcabcabc").span(),
          (0, 3))

        # Hg issue 45
        self.assertEquals(regex.search("^(?:a(?:(?:))+)+", "a").span(), (0, 1))
        self.assertEquals(regex.search("^(?:a(?:(?:))+)+", "aa").span(), (0,
          2))

        # Hg issue 46
        self.assertEquals(regex.search("a(?x: b c )d", "abcd").group(0),
          "abcd")

        # Hg issue 47
        self.assertEquals(regex.search("a#comment\n*", "aaa",
          flags=regex.X).group(0), "aaa")

        # Hg issue 48
        self.assertEquals(regex.search(r"(?V1)(a(?(1)\1)){1}",
          "aaaaaaaaaa").span(0, 1), ((0, 1), (0, 1)))
        self.assertEquals(regex.search(r"(?V1)(a(?(1)\1)){2}",
          "aaaaaaaaaa").span(0, 1), ((0, 3), (1, 3)))
        self.assertEquals(regex.search(r"(?V1)(a(?(1)\1)){3}",
          "aaaaaaaaaa").span(0, 1), ((0, 6), (3, 6)))
        self.assertEquals(regex.search(r"(?V1)(a(?(1)\1)){4}",
          "aaaaaaaaaa").span(0, 1), ((0, 10), (6, 10)))

        # Hg issue 49
        self.assertEquals(regex.search("(?V1)(a)(?<=b(?1))", "baz").group(0),
          "a")

        # Hg issue 50
        self.assertEquals(regex.findall(r'(?fi)\L<keywords>',
          'POST, Post, post, po\u017Ft, po\uFB06, and po\uFB05',
          keywords=['post','pos']), ['POST', 'Post', 'post', 'po\u017Ft',
          'po\uFB06', 'po\uFB05'])
        self.assertEquals(regex.findall(r'(?fi)pos|post',
          'POST, Post, post, po\u017Ft, po\uFB06, and po\uFB05'), ['POS',
          'Pos', 'pos', 'po\u017F', 'po\uFB06', 'po\uFB05'])
        self.assertEquals(regex.findall(r'(?fi)post|pos',
          'POST, Post, post, po\u017Ft, po\uFB06, and po\uFB05'), ['POST',
          'Post', 'post', 'po\u017Ft', 'po\uFB06', 'po\uFB05'])
        self.assertEquals(regex.findall(r'(?fi)post|another',
          'POST, Post, post, po\u017Ft, po\uFB06, and po\uFB05'), ['POST',
          'Post', 'post', 'po\u017Ft', 'po\uFB06', 'po\uFB05'])

        # Hg issue 51
        self.assertEquals(regex.search("(?V1)((a)(?1)|(?2))", "a").group(0, 1,
          2), ('a', 'a', None))

        # Hg issue 52
        self.assertEquals(regex.search(r"(?V1)(\1xx|){6}", "xx").span(0, 1),
          ((0, 2), (2, 2)))

        # Hg issue 53
        self.assertEquals(regex.search("(a|)+", "a").group(0, 1), ("a", ""))

        # Hg issue 54
        self.assertEquals(regex.search(r"(a|)*\d", "a" * 80), None)

        # Hg issue 55
        self.assertEquals(regex.search("^(?:a?b?)*$", "ac"), None)

        # Hg issue 58
        self.assertRaisesRegex(regex.error, self.UNDEF_CHAR_NAME, lambda:
          regex.compile("\\N{1}"))

        # Hg issue 59
        self.assertEquals(regex.search("\\Z", "a\na\n").span(0), (4, 4))

        # Hg issue 60
        self.assertEquals(regex.search("(q1|.)*(q2|.)*(x(a|bc)*y){2,}",
          "xayxay").group(0), "xayxay")

        # Hg issue 61
        self.assertEquals(regex.search("(?i)[^a]", "A"), None)

        # Hg issue 63
        self.assertEquals(regex.search("(?i)[[:ascii:]]", "\N{KELVIN SIGN}"),
          None)

        # Hg issue 66
        self.assertEquals(regex.search("((a|b(?1)c){3,5})", "baaaaca").group(0,
          1, 2), ('aaaa', 'aaaa', 'a'))

        # Hg issue 71
        self.assertEquals(regex.findall(r"(?<=:\S+ )\w+", ":9 abc :10 def"),
          ['abc', 'def'])
        self.assertEquals(regex.findall(r"(?<=:\S* )\w+", ":9 abc :10 def"),
          ['abc', 'def'])
        self.assertEquals(regex.findall(r"(?<=:\S+? )\w+", ":9 abc :10 def"),
          ['abc', 'def'])
        self.assertEquals(regex.findall(r"(?<=:\S*? )\w+", ":9 abc :10 def"),
          ['abc', 'def'])

        # Hg issue 73
        self.assertEquals(regex.search(r"(?:fe)?male", "female").group(),
          "female")
        self.assertEquals([m.group() for m in
          regex.finditer(r"(fe)?male: h(?(1)(er)|(is)) (\w+)",
          "female: her dog; male: his cat. asdsasda")], ['female: her dog',
          'male: his cat'])

        # Hg issue 78
        self.assertEquals(regex.search(r'(?<rec>\((?:[^()]++|(?&rec))*\))',
          'aaa(((1+0)+1)+1)bbb').captures('rec'), ['(1+0)', '((1+0)+1)',
          '(((1+0)+1)+1)'])

        # Hg issue 80
        self.assertRaisesRegex(regex.error, self.BAD_ESCAPE, lambda:
          regex.sub('x', '\\', 'x'), )

        # Hg issue 82
        fz = "(CAGCCTCCCATTTCAGAATATACATCC){1<e<=2}"
        seq = "tcagacgagtgcgttgtaaaacgacggccagtCAGCCTCCCATTCAGAATATACATCCcgacggccagttaaaaacaatgccaaggaggtcatagctgtttcctgccagttaaaaacaatgccaaggaggtcatagctgtttcctgacgcactcgtctgagcgggctggcaagg"
        self.assertEquals(regex.search(fz, seq, regex.BESTMATCH)[0],
          "tCAGCCTCCCATTCAGAATATACATCC")

if sys.version_info < (3, 2, 0):
    # In Python 3.1 it's called assertRaisesRegexp.
    RegexTests.assertRaisesRegex = RegexTests.assertRaisesRegexp

def test_main():
    run_unittest(RegexTests)

if __name__ == "__main__":
    test_main()
