#
# Secret Labs' Regular Expression Engine core module
#
# Copyright (c) 1998-2001 by Secret Labs AB.  All rights reserved.
#
# This version of the SRE library can be redistributed under CNRI's
# Python 1.6 license.  For any other use, please contact Secret Labs
# AB (info@pythonware.com).
#
# Portions of this engine have been developed in cooperation with
# CNRI.  Hewlett-Packard provided funding for 1.6 integration and
# other compatibility work.
#
# 2010-01-16 mrab Python front-end re-written and extended

# Flags.
A = ASCII = 0x80         # Assume ASCII locale.
D = DEBUG = 0x200        # Print parsed pattern.
I = IGNORECASE = 0x2     # Ignore case.
L = LOCALE = 0x4         # Assume current 8-bit locale.
M = MULTILINE = 0x8      # Make anchors look for newline.
N = NEW = 0x100          # Scoped inline flags and correct handling of zero-width matches.
R = REVERSE = 0x400      # Search backwards.
S = DOTALL = 0x10        # Make dot match newline.
U = UNICODE = 0x20       # Assume Unicode locale.
W = WORD = 0x800         # Default Unicode word breaks.
X = VERBOSE = 0x40       # Ignore whitespace and comments.
T = TEMPLATE = 0x1       # Template.

# The mask for the flags.
_GLOBAL_FLAGS = ASCII | DEBUG | LOCALE | NEW | REVERSE | UNICODE
_SCOPED_FLAGS = IGNORECASE | MULTILINE | DOTALL | WORD | VERBOSE

# The regex exception.
class error(Exception):
   pass

# The exception for when a positional flag has been turned on in the old
# behaviour.
class _UnscopedFlagSet(Exception):
    def __init__(self, global_flags):
        Exception.__init__(self)
        self.global_flags = global_flags

# The exception for when parsing fails and we want to try something else.
class ParseError(Exception):
    pass

_ALPHA = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
_DIGITS = frozenset("0123456789")
_ALNUM = _ALPHA | _DIGITS
_OCT_DIGITS = frozenset("01234567")
_HEX_DIGITS = frozenset("0123456789ABCDEFabcdef")
_SPECIAL = frozenset("()[]{}?*+|^$\\")

import sys
import unicodedata
from collections import defaultdict

import _regex

def _shrink_cache(cache_dict, max_length, divisor=5):
    """Make room in the given cache.

    Args:
        cache_dict: The cache dictionary to modify.
        max_length: Maximum # of entries in cache_dict before it is shrunk.
        divisor: Cache will shrink to max_length - 1/divisor*max_length items.
    """
    # Toss out a fraction of the entries at random to make room for new ones.
    # A random algorithm was chosen as opposed to simply cache_dict.popitem()
    # as popitem could penalize the same regular expression repeatedly based
    # on its internal hash value.  Being random should spread the cache miss
    # love around.
    cache_keys = tuple(cache_dict.keys())
    overage = len(cache_keys) - max_length
    if overage < 0:
        # Cache is already within limits.  Normally this should not happen
        # but it could due to multithreading.
        return
    number_to_toss = max_length // divisor + overage
    # The import is done here to avoid a circular dependency.
    import random
    if not hasattr(random, 'sample'):
        # Do nothing while resolving the circular dependency:
        #  re->random->warnings->tokenize->string->re
        return
    for doomed_key in random.sample(cache_keys, number_to_toss):
        try:
            del cache_dict[doomed_key]
        except KeyError:
            # Ignore problems if the cache changed from another thread.
            pass

# The width of the code words inside the regex engine.
_BYTES_PER_CODE = _regex.get_code_size()
_BITS_PER_CODE = _BYTES_PER_CODE * 8

# The repeat count which represents infinity.
_UNLIMITED = (1 << _BITS_PER_CODE) - 1

# The names of the opcodes.
_OPCODES = """\
FAILURE
SUCCESS
ANY
ANY_ALL
ANY_ALL_REV
ANY_REV
ANY_U
ANY_U_REV
ATOMIC
BIG_BITSET
BIG_BITSET_REV
BOUNDARY
BRANCH
CHARACTER
CHARACTER_IGN
CHARACTER_IGN_REV
CHARACTER_REV
DEFAULT_BOUNDARY
END
END_GREEDY_REPEAT
END_GROUP
END_LAZY_REPEAT
END_OF_LINE
END_OF_LINE_U
END_OF_STRING
END_OF_STRING_LINE
END_OF_STRING_LINE_U
GRAPHEME_BOUNDARY
GREEDY_REPEAT
GREEDY_REPEAT_ONE
GROUP
GROUP_EXISTS
LAZY_REPEAT
LAZY_REPEAT_ONE
LOOKAROUND
NEXT
PROPERTY
PROPERTY_REV
REF_GROUP
REF_GROUP_IGN
REF_GROUP_IGN_REV
REF_GROUP_REV
SEARCH_ANCHOR
SET_DIFF
SET_DIFF_REV
SET_INTER
SET_INTER_REV
SET_SYM_DIFF
SET_SYM_DIFF_REV
SET_UNION
SET_UNION_REV
SMALL_BITSET
SMALL_BITSET_REV
START_GROUP
START_OF_LINE
START_OF_LINE_U
START_OF_STRING
STRING
STRING_IGN
STRING_IGN_REV
STRING_REV
"""

def _define_opcodes(opcodes):
    "Defines the opcodes and their numeric values."
    # The namespace for the opcodes.
    class Record:
        pass

    _OP = Record()

    for i, op in enumerate(filter(None, opcodes.splitlines())):
        setattr(_OP, op, i)

    return _OP

# Define the opcodes in a namespace.
_OP = _define_opcodes(_OPCODES)

# The regular expression flags.
_REGEX_FLAGS = {"a": ASCII, "i": IGNORECASE, "L": LOCALE, "m": MULTILINE, "n":
  NEW, "r": REVERSE, "s": DOTALL, "u": UNICODE, "w": WORD, "x": VERBOSE}

def _all_cases(info, ch):
    return _regex.all_cases(info.global_flags, ch)

def _compile_firstset(info, fs):
    "Compiles the firstset for the pattern."
    if not fs or _VOID_ITEM in fs or None in fs:
        # No firstset.
        return []
    characters, properties = [], []
    for m in fs:
        t = type(m)
        if t is _Character and m.positive:
            characters.append(m.value)
        elif t is _Property:
            properties.append(m)
        elif t is _CharacterIgn and m.positive:
            characters.extend(_all_cases(info, m.value))
        elif t is _SetUnion and m.positive:
            for i in m.items:
                if isinstance(i, _Character):
                    characters.append(i.value)
                elif isinstance(i, _Property):
                    properties.append(i)
                else:
                    return []
        else:
            return []
    items = [_Character(c) for c in set(characters)] + list(set(properties))
    if items:
        fs = _SetUnion(items, zerowidth=True)
    else:
        # No firstset.
        return []
    fs = fs.optimise(info)
    if not fs:
        # No firstset.
        return []
    rev = bool(info.global_flags & REVERSE)
    # Compile the firstset.
    return fs.compile(rev)

def _count_ones(n):
    "Counts the number of set bits in an int."
    count = 0
    while n:
        count += 1
        n &= n - 1
    return count

def _flatten_code(code):
    "Flattens the code from a list of tuples."
    flat_code = []
    for c in code:
        flat_code.extend(c)
    return flat_code

def _parse_pattern(source, info):
    "Parses a pattern, eg. 'a|b|c'."
    # Capture group names can be duplicated provided that their matching is
    # mutually exclusive.
    previous_groups = info.used_groups.copy()
    branches = [_parse_sequence(source, info)]
    all_groups = info.used_groups
    while source.match("|"):
        info.used_groups = previous_groups.copy()
        branches.append(_parse_sequence(source, info))
        all_groups |= info.used_groups
    info.used_groups = all_groups
    if len(branches) == 1:
        return branches[0]
    return _Branch(branches)

def _parse_sequence(source, info):
    "Parses a sequence, eg. 'abc'."
    sequence = []
    item = _parse_item(source, info)
    while item:
        sequence.append(item)
        item = _parse_item(source, info)
    if len(sequence) == 1:
        return sequence[0]
    return _Sequence(sequence)

def _PossessiveRepeat(element, min_count, max_count):
    return _Atomic(_GreedyRepeat(element, min_count, max_count))

def _parse_item(source, info):
    "Parses an item, which might be repeated. Returns None if there's no item."
    element = _parse_element(source, info)
    counts = _parse_quantifier(source, info)
    if not counts:
        # No quantifier.
        return element
    if not element or not element.can_repeat():
        raise error("nothing to repeat")
    min_count, max_count = counts
    here = source.pos
    ch = source.get()
    if ch == "?":
        # The "?" suffix that means it's a lazy repeat.
        repeated = _LazyRepeat
    elif ch == "+":
        # The "+" suffix that means it's a possessive repeat.
        repeated = _PossessiveRepeat
    else:
        # No suffix means that it's a greedy repeat.
        source.pos = here
        repeated = _GreedyRepeat
    if min_count == max_count == 1:
        # Only ever one repeat.
        return element
    return repeated(element, min_count, max_count)

def _parse_quantifier(source, info):
    "Parses a quantifier."
    here = source.pos
    ch = source.get()
    if ch == "?":
        # Optional element, eg. 'a?'.
        return 0, 1
    if ch == "*":
        # Repeated element, eg. 'a*'.
        return 0, None
    if ch == "+":
        # Repeated element, eg. 'a+'.
        return 1, None
    if ch == "{":
        # Looks like a limited repeated element, eg. 'a{2,3}'.
        min_count = _parse_count(source)
        ch = source.get()
        if ch == ",":
            max_count = _parse_count(source)
            if not source.match("}"):
                # Not a quantifier, so parse it later as a literal.
                source.pos = here
                return None
            # No minimum means 0 and no maximum means unlimited.
            min_count = int(min_count) if min_count else 0
            max_count = int(max_count) if max_count else None
            if max_count is not None and min_count > max_count:
                raise error("min repeat greater than max repeat")
            if min_count >= _UNLIMITED or max_count is not None and max_count \
              >= _UNLIMITED:
                raise error("repeat count too big")
            return min_count, max_count
        if ch == "}":
            if not min_count:
                # Not a quantifier, so parse it later as a literal.
                source.pos = here
                return None
            min_count = max_count = int(min_count)
            if min_count >= _UNLIMITED:
                raise error("repeat count too big")
            return min_count, max_count
    # No quantifier.
    source.pos = here
    return None

def _parse_count(source):
    "Parses a quantifier's count, which can be empty."
    count = []
    here = source.pos
    ch = source.get()
    while ch in _DIGITS:
        count.append(ch)
        here = source.pos
        ch = source.get()
    source.pos = here
    return "".join(count)

_SPECIAL_CHARS = set("()|?*+{^$.[\\#") | set([""])

def _parse_element(source, info):
    "Parses an element. An element might actually be a flag, eg. '(?i)'."
    while True:
        here = source.pos
        ch = source.get()
        if ch in _SPECIAL_CHARS:
            if ch in ")|":
                # The end of a sequence. At the end of the pattern ch is "".
                source.pos = here
                return None
            elif ch == "\\":
                # An escape sequence.
                return _parse_escape(source, info, False)
            elif ch == "(":
                # A parenthesised subpattern or a flag.
                element = _parse_paren(source, info)
                if element:
                    return element
            elif ch == ".":
                # Any character.
                if info.all_flags & DOTALL:
                    return _AnyAll()
                elif info.all_flags & WORD:
                    return _AnyU()
                else:
                    return _Any()
            elif ch == "[":
                # A character set.
                return _parse_set(source, info)
            elif ch == "^":
                # The start of a line or the string.
                if info.all_flags & MULTILINE:
                    if info.all_flags & WORD:
                        return _StartOfLineU()
                    else:
                        return _StartOfLine()
                else:
                    return _StartOfString()
            elif ch == "$":
                # The end of a line or the string.
                if info.all_flags & MULTILINE:
                    if info.all_flags & WORD:
                        return _EndOfLineU()
                    else:
                        return _EndOfLine()
                else:
                    if info.all_flags & WORD:
                        return _EndOfStringLineU()
                    else:
                        return _EndOfStringLine()
            elif ch == "{":
                # Looks like a limited quantifier.
                here2 = source.pos
                source.pos = here
                counts = _parse_quantifier(source, info)
                if counts:
                    # A quantifier where we expected an element.
                    raise error("nothing to repeat")
                # Not a quantifier, so it's a literal.
                source.pos = here2
                return _Character(ord(ch))
            elif ch in "?*+":
                # A quantifier where we expected an element.
                raise error("nothing to repeat")
            elif info.all_flags & VERBOSE:
                if ch == "#":
                    # A comment.
                    source.ignore_space = False
                    # Ignore characters until a newline or the end of the pattern.
                    while source.get() not in "\n":
                        pass
                    source.ignore_space = True
                else:
                    # A literal.
                    if info.all_flags & IGNORECASE:
                        return _CharacterIgn(ord(ch))
                    return _Character(ord(ch))
            else:
                # A literal.
                if info.all_flags & IGNORECASE:
                    return _CharacterIgn(ord(ch))
                return _Character(ord(ch))
        else:
            # A literal.
            if info.all_flags & IGNORECASE:
                return _CharacterIgn(ord(ch))
            return _Character(ord(ch))

def _parse_paren(source, info):
    "Parses a parenthesised subpattern or a flag."
    here = source.pos
    ch = source.get()
    if ch == "?":
        here2 = source.pos
        ch = source.get()
        if ch == "<":
            here3 = source.pos
            ch = source.get()
            if ch == "=":
                # Positive lookbehind.
                return _parse_lookaround(source, info, True, True)
            if ch == "!":
                # Negative lookbehind.
                return _parse_lookaround(source, info, True, False)
            # A named capture group.
            source.pos = here3
            name = _parse_name(source)
            group = info.new_group(name)
            source.expect(">")
            saved_scoped_flags = info.scoped_flags
            saved_ignore = source.ignore_space
            try:
                subpattern = _parse_pattern(source, info)
            finally:
                info.scoped_flags = saved_scoped_flags
                source.ignore_space = saved_ignore
            source.expect(")")
            info.close_group(group)
            return _Group(info, group, subpattern)
        if ch == "=":
            # Positive lookahead.
            return _parse_lookaround(source, info, False, True)
        if ch == "!":
            # Negative lookahead.
            return _parse_lookaround(source, info, False, False)
        if ch == "P":
            # A Python extension.
            return _parse_extension(source, info)
        if ch == "#":
            # A comment.
            return _parse_comment(source)
        if ch == "(":
            # A conditional subpattern.
            return _parse_conditional(source, info)
        if ch == ">":
            # An atomic subpattern.
            return _parse_atomic(source, info)
        if ch == "|":
            # A common groups branch.
            return _parse_common(source, info)
        # A flags subpattern.
        source.pos = here2
        return _parse_flags_subpattern(source, info)
    # An unnamed capture group.
    source.pos = here
    group = info.new_group()
    saved_scoped_flags = info.scoped_flags
    saved_ignore = source.ignore_space
    try:
        subpattern = _parse_pattern(source, info)
    finally:
        info.scoped_flags = saved_scoped_flags
        info.all_flags = info.global_flags | info.scoped_flags
        source.ignore_space = saved_ignore
    source.expect(")")
    info.close_group(group)
    return _Group(info, group, subpattern)

def _parse_extension(source, info):
    "Parses a Python extension."
    here = source.pos
    ch = source.get()
    if ch == "<":
        # A named capture group.
        name = _parse_name(source)
        group = info.new_group(name)
        source.expect(">")
        saved_scoped_flags = info.scoped_flags
        saved_ignore = source.ignore_space
        try:
            subpattern = _parse_pattern(source, info)
        finally:
            info.scoped_flags = saved_scoped_flags
            source.ignore_space = saved_ignore
        source.expect(")")
        info.close_group(group)
        return _Group(info, group, subpattern)
    if ch == "=":
        # A named group reference.
        name = _parse_name(source)
        source.expect(")")
        if info.is_open_group(name):
            raise error("can't refer to an open group")
        if info.all_flags & IGNORECASE:
            return _RefGroupIgn(info, name)
        return _RefGroup(info, name)
    source.pos = here
    raise error("unknown extension")

def _parse_comment(source):
    "Parses a comment."
    ch = source.get()
    while ch not in ")":
        ch = source.get()
    if not ch:
        raise error("missing )")
    return None

def _parse_lookaround(source, info, behind, positive):
    "Parses a lookaround."
    saved_scoped_flags = info.scoped_flags
    saved_ignore = source.ignore_space
    try:
        subpattern = _parse_pattern(source, info)
    finally:
        info.scoped_flags = saved_scoped_flags
        source.ignore_space = saved_ignore
    source.expect(")")
    return _LookAround(behind, positive, subpattern)

def _parse_conditional(source, info):
    "Parses a conditional subpattern."
    saved_scoped_flags = info.scoped_flags
    saved_ignore = source.ignore_space
    try:
        group = _parse_name(source, True)
        source.expect(")")
        previous_groups = info.used_groups.copy()
        yes_branch = _parse_sequence(source, info)
        if source.match("|"):
            yes_groups = info.used_groups
            info.used_groups = previous_groups
            no_branch = _parse_sequence(source, info)
            info.used_groups |= yes_groups
        else:
            no_branch = None
    finally:
        info.scoped_flags = saved_scoped_flags
        source.ignore_space = saved_ignore
    source.expect(")")
    return _Conditional(info, group, yes_branch, no_branch)

def _parse_atomic(source, info):
    "Parses an atomic subpattern."
    saved_scoped_flags = info.scoped_flags
    saved_ignore = source.ignore_space
    try:
        subpattern = _parse_pattern(source, info)
    finally:
        info.scoped_flags = saved_scoped_flags
        source.ignore_space = saved_ignore
    source.expect(")")
    return _Atomic(subpattern)

def _parse_common(source, info):
    "Parses a common groups branch."
    # Capture group numbers in different branches can reuse the group numbers.
    previous_groups = info.used_groups.copy()
    initial_group_count = info.group_count
    branches = [_parse_sequence(source, info)]
    final_group_count = info.group_count
    all_groups = info.used_groups
    while source.match("|"):
        info.used_groups = previous_groups.copy()
        info.group_count = initial_group_count
        branches.append(_parse_sequence(source, info))
        final_group_count = max(final_group_count, info.group_count)
        all_groups |= info.used_groups
    info.used_groups = all_groups
    info.group_count = final_group_count
    source.expect(")")
    if len(branches) == 1:
        return branches[0]
    return _Branch(branches)

def _parse_flags_subpattern(source, info):
    "Parses a flags subpattern."
    # It could be inline flags or a subpattern possibly with local flags.
    # Parse the flags.
    flags_on, flags_off = 0, 0
    try:
        while True:
            here = source.pos
            ch = source.get()
            flags_on |= _REGEX_FLAGS[ch]
    except KeyError:
        pass
    if ch == "-":
        try:
            while True:
                here = source.pos
                ch = source.get()
                flags_off |= _REGEX_FLAGS[ch]
        except KeyError:
            pass
        if not flags_off or (flags_off & _GLOBAL_FLAGS):
            error("bad inline flags")

    # Separate the global and scoped flags.
    source.pos = here
    old_global_flags = info.global_flags
    info.global_flags |= flags_on & _GLOBAL_FLAGS
    flags_on &= _SCOPED_FLAGS
    flags_off &= _SCOPED_FLAGS
    new_scoped_flags = (info.scoped_flags | flags_on) & ~flags_off
    saved_scoped_flags = info.scoped_flags
    saved_ignore = source.ignore_space
    info.scoped_flags = new_scoped_flags
    info.all_flags = info.global_flags | info.scoped_flags
    source.ignore_space = bool(info.all_flags & VERBOSE)
    if source.match(":"):
        # A subpattern with local flags.
        saved_global_flags = info.global_flags
        info.global_flags &= ~flags_off
        info.all_flags = info.global_flags | info.scoped_flags
        try:
            subpattern = _parse_pattern(source, info)
        finally:
            info.global_flags = saved_global_flags
            info.scoped_flags = saved_scoped_flags
            info.all_flags = info.global_flags | info.scoped_flags
            source.ignore_space = saved_ignore
        source.expect(")")
        return subpattern
    else:
        # Positional flags.
        if not source.match(")"):
            raise error("bad inline flags")
        new_behaviour = bool(info.global_flags & NEW)
        if not new_behaviour:
            # Old behaviour: positional flags are global and can only be turned
            # on.
            info.global_flags |= flags_on
        if info.global_flags & ~old_global_flags:
            # A global has been turned on, so reparse the pattern.
            if new_behaviour:
                # New behaviour: positional flags are scoped.
                info.global_flags &= _GLOBAL_FLAGS
            raise _UnscopedFlagSet(info.global_flags)
        info.all_flags = info.global_flags | info.scoped_flags
        return None

def _parse_name(source, allow_numeric=False):
    "Parses a name."
    saved_ignore = source.ignore_space
    source.ignore_space = False
    name = []
    here = source.pos
    ch = source.get()
    while ch in _ALNUM or ch == "_":
        name.append(ch)
        here = source.pos
        ch = source.get()
    source.pos = here
    source.ignore_space = saved_ignore
    name = "".join(name)
    if not name:
        raise error("bad group name")
    if name.isdigit():
        if not allow_numeric:
            raise error("bad group name")
    else:
        if name[0].isdigit():
            raise error("bad group name")
    return name

def _is_octal(string):
    "Checks whether a string is octal."
    return all(ch in _OCT_DIGITS for ch in string)

def _is_decimal(string):
    "Checks whether a string is decimal."
    return all(ch in _DIGITS for ch in string)

def _is_hexadecimal(string):
    "Checks whether a string is hexadecimal."
    return all(ch in _HEX_DIGITS for ch in string)

def _parse_escape(source, info, in_set):
    "Parses an escape sequence."
    ch = source.get()
    if not ch:
        # A backslash at the end of the pattern.
        raise error("bad escape")
    if ch == "x":
        # A 2-digit hexadecimal escape sequence.
        return _parse_hex_escape(source, info, 2, in_set)
    elif ch == "u":
        # A 4-digit hexadecimal escape sequence.
        return _parse_hex_escape(source, info, 4, in_set)
    elif ch == "U":
        # A 8-digit hexadecimal escape sequence.
        return _parse_hex_escape(source, info, 8, in_set)
    elif ch == "g" and not in_set:
        # A group reference.
        here = source.pos
        try:
            return _parse_group_ref(source, info)
        except error:
            # Invalid as a group reference, so assume it's a literal.
            source.pos = here
            return _char_literal(info, in_set, ch)
    elif ch == "G" and not in_set:
        # A search anchor.
        return _SearchAnchor()
    elif ch == "N":
        # A named codepoint.
        return _parse_named_char(source, info, in_set)
    elif ch in "pP":
        # A Unicode property.
        return _parse_property(source, info, in_set, ch == "p")
    elif ch == "X" and not in_set:
        # A grapheme cluster.
        return _Grapheme()
    elif ch in _ALPHA:
        # An alphabetic escape sequence.
        # Positional escapes aren't allowed inside a character set.
        if not in_set:
            if info.all_flags & WORD:
                value = _WORD_POSITION_ESCAPES.get(ch)
            else:
                value = _POSITION_ESCAPES.get(ch)
            if value:
                return value
        value = _CHARSET_ESCAPES.get(ch)
        if value:
            return value
        value = _CHARACTER_ESCAPES.get(ch)
        if value:
            return _Character(ord(value))
        return _char_literal(info, in_set, ch)
    elif ch in _DIGITS:
        # A numeric escape sequence.
        return _parse_numeric_escape(source, info, ch, in_set)
    else:
        # A literal.
        return _char_literal(info, in_set, ch)

def _char_literal(info, in_set, ch):
    "Creates a character literal, which might be in a set."
    if (info.all_flags & IGNORECASE) and not in_set:
        return _CharacterIgn(ord(ch))
    return _Character(ord(ch))

def _parse_numeric_escape(source, info, ch, in_set):
    "Parses a numeric escape sequence."
    if in_set or ch == "0":
        # Octal escape sequence, max 3 digits.
        return _parse_octal_escape(source, info, [ch], in_set)
    # At least 1 digit, so either octal escape or group.
    digits = ch
    here = source.pos
    ch = source.get()
    if ch in _DIGITS:
        # At least 2 digits, so either octal escape or group.
        digits += ch
        here = source.pos
        ch = source.get()
        if _is_octal(digits) and ch in _OCT_DIGITS:
            # 3 octal digits, so octal escape sequence.
            value = int(digits + ch, 8) & 0xFF
            if info.all_flags & IGNORECASE:
                return _CharacterIgn(value)
            return _Character(value)
        else:
            # 2 digits, so group.
            source.pos = here
            if info.is_open_group(digits):
                raise error("can't refer to an open group")
            if info.all_flags & IGNORECASE:
                return _RefGroupIgn(info, digits)
            return _RefGroup(info, digits)
    # 1 digit, so group.
    source.pos = here
    if info.is_open_group(digits):
        raise error("can't refer to an open group")
    if info.all_flags & IGNORECASE:
        return _RefGroupIgn(info, digits)
    return _RefGroup(info, digits)

def _parse_octal_escape(source, info, digits, in_set):
    "Parses an octal escape sequence."
    here = source.pos
    ch = source.get()
    while len(digits) < 3 and ch in _OCT_DIGITS:
        digits.append(ch)
        here = source.pos
        ch = source.get()
    source.pos = here
    try:
        value = int("".join(digits), 8) & 0xFF
        if (info.all_flags & IGNORECASE) and not in_set:
            return _CharacterIgn(value)
        return _Character(value)
    except ValueError:
        raise error("bad escape")

def _parse_hex_escape(source, info, max_len, in_set):
    "Parses a hex escape sequence."
    digits = []
    here = source.pos
    ch = source.get()
    while len(digits) < max_len and ch in _HEX_DIGITS:
        digits.append(ch)
        here = source.pos
        ch = source.get()
    if len(digits) != max_len:
        raise error("bad hex escape")
    source.pos = here
    value = int("".join(digits), 16)
    if (info.all_flags & IGNORECASE) and not in_set:
        return _CharacterIgn(value)
    return _Character(value)

def _parse_group_ref(source, info):
    "Parses a group reference."
    source.expect("<")
    name = _parse_name(source, True)
    source.expect(">")
    if info.is_open_group(name):
        raise error("can't refer to an open group")
    if info.all_flags & IGNORECASE:
        return _RefGroupIgn(info, name)
    return _RefGroup(info, name)

def _parse_named_char(source, info, in_set):
    "Parses a named character."
    here = source.pos
    ch = source.get()
    if ch == "{":
        name = []
        ch = source.get()
        while ch in _ALPHA or ch == " ":
            name.append(ch)
            ch = source.get()
        if ch == "}":
            try:
                value = unicodedata.lookup("".join(name))
                if (info.all_flags & IGNORECASE) and not in_set:
                    return _CharacterIgn(ord(value))
                return _Character(ord(value))
            except KeyError:
                raise error("undefined character name")
    source.pos = here
    return _char_literal(info, in_set, "N")

def _parse_property(source, info, in_set, positive):
    "Parses a Unicode property."
    here = source.pos
    if source.match("{"):
        negate = source.match("^")
        prop_name, name = _parse_property_name(source)
        if source.match("}"):
            # It's correctly delimited.
            return _lookup_property(prop_name, name, positive != negate)

    # Not a property, so treat as a literal "p" or "P".
    source.pos = here
    ch = "p" if positive else "P"
    return _char_literal(info, in_set, ch)

def _parse_property_name(source):
    "Parses a property name, which may be qualified."
    name = []
    here = source.pos
    ch = source.get()
    while ch and (ch in _ALNUM or ch in " &_-."):
        name.append(ch)
        here = source.pos
        ch = source.get()

    here2 = here
    if ch and ch in ":=":
        prop_name = name
        name = []
        here = source.pos
        ch = source.get()
        while ch and (ch in _ALNUM or ch in " &_-."):
            name.append(ch)
            here = source.pos
            ch = source.get()
        if all(ch == " " for ch in name):
            # No name after the ":" or "=", so assume it's an unqualified name.
            prop_name, name = None, prop_name
            here = here2
    else:
        prop_name = None

    source.pos = here
    return prop_name, name

def _parse_set(source, info):
    "Parses a character set."
    saved_ignore = source.ignore_space
    source.ignore_space = False
    try:
        item = _parse_set_union(source, info)
    finally:
        source.ignore_space = saved_ignore
    return item

def _parse_set_union(source, info):
    "Parses a set union ([x||y])."
    # Negative set?
    negate = source.match("^")
    items = [_parse_set_symm_diff(source, info)]
    while source.match("||"):
        items.append(_parse_set_symm_diff(source, info))
    if not source.match("]"):
        raise error("missing ]")
    item = _SetUnion(items, positive=not negate)
    return item

def _parse_set_symm_diff(source, info):
    "Parses a set symmetric difference ([x~~y])."
    items = [_parse_set_inter(source, info)]
    while source.match("~~"):
        items.append(_parse_set_inter(source, info))
    return _SetSymDiff(items)

def _parse_set_inter(source, info):
    "Parses a set intersection ([x&&y])."
    items = [_parse_set_diff(source, info)]
    while source.match("&&"):
        items.append(_parse_set_diff(source, info))
    return _SetInter(items)

def _parse_set_diff(source, info):
    "Parses a set difference ([x--y])."
    items = [_parse_set_imp_union(source, info)]
    while source.match("--"):
        items.append(_parse_set_imp_union(source, info))
    return _SetDiff(items)

_SET_OPS = ("||", "~~", "&&", "--")

def _parse_set_imp_union(source, info):
    "Parses a set implicit union ([xy])."
    items = [_parse_set_member(source, info)]
    while True:
        here = source.pos
        if source.match("]") or any(source.match(op) for op in _SET_OPS):
            break
        items.append(_parse_set_member(source, info))
    source.pos = here
    return _SetUnion(items)

def _parse_set_member(source, info):
    "Parses a member in a character set."
    # Parse a character or property.
    start = _parse_set_item(source, info)
    if not isinstance(start, _Character):
        # Not the start of a range.
        return start
    if not source.match("-"):
        # Not a range.
        if info.all_flags & IGNORECASE:
            # Case-insensitive.
            characters = _all_cases(info, start.value)
            # Is it a caseless character?
            if len(characters) == 1:
                return start
            return _SetUnion([_Character(c) for c in characters])
        return start
    # It looks like the start of a range of characters.
    here = source.pos
    if source.match("]"):
        # We've reached the end of the set, so return both the character and
        # hyphen.
        source.pos = here
        characters = [ord("-")]
        if info.all_flags & IGNORECASE:
            # Case-insensitive.
            characters.extend(_all_cases(info, start.value))
        return _SetUnion([_Character(c) for c in characters])
    # Parse a character or property.
    end = _parse_set_item(source, info)
    if not isinstance(end, _Character):
        # It's not a range, so return the character, hyphen and property.
        characters = [ord("-")]
        if info.all_flags & IGNORECASE:
            # Case-insensitive.
            characters.extend(_all_cases(info, start.value))
        return _SetUnion([_Character(c) for c in characters] + [end])
    # It _is_ a range.
    if start.value > end.value:
        raise error("bad character range")
    characters = list(range(start.value, end.value + 1))
    if info.all_flags & IGNORECASE:
        for c in range(start.value, end.value + 1):
            characters.extend(_all_cases(info, c))
    return _SetUnion([_Character(c) for c in characters])

def _parse_set_item(source, info):
    "Parses an item in a character set."
    if source.match("\\"):
        return _parse_escape(source, info, True)
    here = source.pos
    if source.match("[:"):
        # Looks like a POSIX character class.
        try:
            return _parse_posix_class(source, info)
        except ParseError:
            # Not a POSIX character class.
            source.pos = here
    ch = source.get()
    if ch == "[":
        # Looks like the start of a nested set.
        here = source.pos
        try:
            return _parse_set_union(source, info)
        except error:
            # Failed to parse a nested set, so treat it as a literal.
            source.pos = here
    if not ch:
        raise error("bad set")
    return _Character(ord(ch))

def _parse_posix_class(source, info):
    "Parses a POSIX character class."
    negate = source.match("^")
    prop_name, name = _parse_property_name(source)
    if not source.match(":]"):
        raise ParseError()
    return _lookup_property(prop_name, name, not negate)

def _float_to_rational(flt):
    "Converts a float to a rational pair."
    int_part = int(flt)
    error = flt - int_part
    if abs(error) < 0.0001:
        return int_part, 1
    den, num = _float_to_rational(1.0 / error)
    return int_part * den + num, den

def _numeric_to_rational(numeric):
    "Converts a numeric string to a rational string, if possible."
    if numeric[0] == "-":
        sign, numeric = numeric[0], numeric[1 : ]
    else:
        sign = ""

    parts = numeric.split("/")
    if len(parts) == 2:
        num, den = _float_to_rational(float(parts[0]) / float(parts[1]))
    elif len(parts) == 1:
        num, den = _float_to_rational(float(parts[0]))
    else:
        raise ValueError

    format = "{}{}" if den == 1 else "{}{}/{}"

    return format.format(sign, num, den)

def _standardise_name(name):
    "Standardises a property or value name."
    try:
        return _numeric_to_rational("".join(name))
    except (ValueError, ZeroDivisionError):
        return "".join(ch for ch in name if ch not in "_- ").upper()

def _lookup_property(property, value, positive):
    "Looks up a property."
    # Normalise the names (which may still be lists).
    property = _standardise_name(property) if property else None
    value = _standardise_name(value)
    if property:
        # Both the property and the value are provided.
        prop = _properties.get(property)
        if not prop:
            raise error("unknown property")
        prop_id, value_dict = prop
        val_id = value_dict.get(value)
        if val_id is None:
            raise error("unknown property value")
        return _Property((prop_id << 16) | val_id, positive)

    # Only the value is provided.
    # It might be the name of a GC, script or block value.
    for property in ("GC", "SCRIPT", "BLOCK"):
        prop_id, value_dict = _properties.get(property)
        val_id = value_dict.get(value)
        if val_id is not None:
            return _Property((prop_id << 16) | val_id, positive)

    # It might be the name of a property.
    prop = _properties.get(value)
    if prop:
        prop_id, value_dict = prop
        return _Property(prop_id << 16, not positive)

    # It might be the name of a binary property.
    if value.startswith("IS"):
        prop = _properties.get(value[2 : ])
        if prop:
            prop_id, value_dict = prop
            return _Property(prop_id << 16, not positive)

    # It might be the prefixed name of a script or block.
    for prefix, property in (("IS", "SCRIPT"), ("IN", "BLOCK")):
        if value.startswith(prefix):
            prop_id, value_dict = _properties.get(property)
            val_id = value_dict.get(value[2 : ])
            if val_id is not None:
                return _Property((prop_id << 16) | val_id, positive)

    # Unknown property.
    raise error("unknown property")

def _compile_repl_escape(source, pattern):
    "Compiles a replacement template escape sequence."
    ch = source.get()
    if ch in _ALPHA:
        # An alphabetic escape sequence.
        value = _CHARACTER_ESCAPES.get(ch)
        if value:
            return False, [ord(value)]
        if ch == "g":
            # A group preference.
            return True, [_compile_repl_group(source, pattern)]
        return False, [ord("\\"), ord(ch)]
    if ch == "0":
        # An octal escape sequence.
        digits = ch
        while len(digits) < 3:
            here = source.pos
            ch = source.get()
            if ch not in _OCT_DIGITS:
                source.pos = here
                break
            digits += ch
        return False, [int(digits, 8) & 0xFF]
    if ch in _DIGITS:
        # Either an octal escape sequence (3 digits) or a group reference (max
        # 2 digits).
        digits = ch
        here = source.pos
        ch = source.get()
        if ch in _DIGITS:
            digits += ch
            here = source.pos
            ch = source.get()
            if ch and _is_octal(digits + ch):
                # An octal escape sequence.
                return False, [int(digits + ch, 8) & 0xFF]
        # A group reference.
        source.pos = here
        return True, [int(digits)]
    if ch == "\\":
        # An escaped backslash is a backslash.
        return False, [ord("\\")]
    # An escaped non-backslash is a backslash followed by the literal.
    return False, [ord("\\"), ord(ch)]

def _compile_repl_group(source, pattern):
    "Compiles a replacement template group reference."
    source.expect("<")
    name = _parse_name(source, True)
    source.expect(">")
    if name.isdigit():
        index = int(name)
        if not 0 <= index <= pattern.groups:
            raise error("invalid group")
        return index
    try:
        return pattern.groupindex[name]
    except KeyError:
        raise IndexError("unknown group")

# The regular expression is parsed into a syntax tree. The different types of
# node are defined below.

_INDENT = "  "
_ZEROWIDTH_OP = 0x2

_VOID_ITEM = object()

# Common base for all nodes.
class _RegexBase:
    def __init__(self):
        self._key = self.__class__
    def fix_groups(self):
        pass
    def optimise(self, info):
        return self
    def pack_characters(self):
        return self
    def remove_captures(self):
        return self
    def is_empty(self):
        return False
    def is_atomic(self):
        return True
    def contains_group(self):
        return False
    def get_first(self):
        return self
    def drop_first(self):
        return _Sequence()
    def get_last(self):
        return self
    def drop_last(self):
        return _Sequence()
    def can_repeat(self):
        return True
    def firstset(self):
        return set([_VOID_ITEM])
    def has_simple_start(self):
        return False
    def __hash__(self):
        return hash(self._key)
    def __eq__(self, other):
        return type(self) is type(other) and self._key == other._key
    def __ne__(self, other):
        return not self.__eq__(other)

# Base for zero-width nodes.
class _ZeroWidthBase(_RegexBase):
    def firstset(self):
        return set([None])
    def can_repeat(self):
        return False

# Base for 'structure' nodes, ie those containing subpatterns.
class _StructureBase(_RegexBase):
    def get_first(self):
        return None
    def drop_first(self):
        raise error("internal error")
    def get_last(self):
        return None
    def drop_last(self):
        raise error("internal error")

class _Any(_RegexBase):
    _opcode = {False: _OP.ANY, True: _OP.ANY_REV}
    _op_name = {False: "ANY", True: "ANY_REV"}
    def compile(self, reverse=False):
        return [(self._opcode[reverse], )]
    def dump(self, indent=0, reverse=False):
        print("{}{}".format(_INDENT * indent, self._op_name[reverse]))
    def has_simple_start(self):
        return True

class _AnyAll(_Any):
    _opcode = {False: _OP.ANY_ALL, True: _OP.ANY_ALL_REV}
    _op_name = {False: "ANY_ALL", True: "ANY_ALL_REV"}

class _AnyU(_Any):
    _opcode = {False: _OP.ANY_U, True: _OP.ANY_U_REV}
    _op_name = {False: "ANY_U", True: "ANY_U_REV"}

class _Atomic(_StructureBase):
    def __init__(self, subpattern):
        self.subpattern = subpattern
        self._optimised = False
    def fix_groups(self):
        self.subpattern.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        sequence = self.subpattern.optimise(info)
        prefix, sequence = _Atomic._split_atomic_prefix(sequence)
        suffix, sequence = _Atomic._split_atomic_suffix(sequence)
        # Is there anything left in the atomic sequence?
        if sequence.is_empty():
            sequence = []
        else:
            sequence = [_Atomic(sequence)]
        sequence = prefix + sequence + suffix
        if len(sequence) == 1:
            return sequence[0]
        return _Sequence(sequence)
    def pack_characters(self):
        self.subpattern = self.subpattern.pack_characters()
        return self
    def is_empty(self):
        return self.subpattern.is_empty()
    def contains_group(self):
        return self.subpattern.contains_group()
    def compile(self, reverse=False):
        return [(_OP.ATOMIC, )] + self.subpattern.compile(reverse) + [(_OP.END,
          )]
    def dump(self, indent=0, reverse=False):
        print("{}{}".format(_INDENT * indent, "ATOMIC"))
        self.subpattern.dump(indent + 1, reverse)
    def firstset(self):
        return self.subpattern.firstset()
    def has_simple_start(self):
        return self.subpattern.has_simple_start()
    def __eq__(self, other):
        return type(self) is type(other) and self.subpattern == other.subpattern
    @staticmethod
    def _split_atomic_prefix(sequence):
        # Leading atomic items can be moved out of an atomic sequence.
        prefix = []
        while True:
            item = sequence.get_first()
            if not item or not item.is_atomic():
                break
            prefix.append(item)
            sequence = sequence.drop_first()
        return prefix, sequence
    @staticmethod
    def _split_atomic_suffix(sequence):
        # Trailing atomic items can be moved out of an atomic sequence.
        suffix = []
        while True:
            item = sequence.get_last()
            if not item or not item.is_atomic():
                break
            suffix.append(item)
            sequence = sequence.drop_last()
        return list(reversed(suffix)), sequence

class _Boundary(_ZeroWidthBase):
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    def __init__(self, positive=True):
        self.positive = bool(positive)
        self._key = self.__class__, self.positive
    def compile(self, reverse=False):
        return [(_OP.BOUNDARY, int(self.positive))]
    def dump(self, indent=0, reverse=False):
        print("{}BOUNDARY {}".format(_INDENT * indent,
          self._pos_text[self.positive]))

class _Branch(_StructureBase):
    def __init__(self, branches):
        self.branches = branches
        self._optimised = False
    def fix_groups(self):
        for branch in self.branches:
            branch.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        branches = _Branch._flatten_branches(info, self.branches)
        prefix, branches = _Branch._split_common_prefix(branches)
        suffix, branches = _Branch._split_common_suffix(branches)
        branches = _Branch._merge_character_prefixes(info, branches)
        branches = _Branch._reduce_to_set(info, branches)
        if len(branches) > 1:
            branches = [_Branch(branches)]
        elif len(branches) == 1:
            branches = [branches[0]]
        sequence = prefix + branches + suffix
        if len(sequence) == 1:
            return sequence[0]
        return _Sequence(sequence)
    def pack_characters(self):
        self.branches = [branch.pack_characters() for branch in self.branches]
        return self
    def is_empty(self):
        return all(branch.is_empty() for branch in self.branches)
    def is_atomic(self):
        return all(branch.is_atomic() for branch in self.branches)
    def contains_group(self):
        return any(branch.contains_group() for branch in self.branches)
    def compile(self, reverse=False):
        code = [(_OP.BRANCH, )]
        for branch in self.branches:
            code.extend(branch.compile(reverse))
            code.append((_OP.NEXT, ))
        code[-1] = (_OP.END, )
        return code
    def remove_captures(self):
        self.branches = [branch.remove_captures() for branch in self.branches]
        return self
    def dump(self, indent=0, reverse=False):
        print("{}BRANCH".format(_INDENT * indent))
        self.branches[0].dump(indent + 1, reverse)
        for branch in self.branches[1 : ]:
            print("{}OR".format(_INDENT * indent))
            branch.dump(indent + 1, reverse)
    def firstset(self):
        fs = set()
        for branch in self.branches:
            fs |= branch.firstset()
        return fs or set([None])
    def __eq__(self, other):
        return type(self) is type(other) and self.branches == other.branches
    @staticmethod
    def _flatten_branches(info, branches):
        # Flatten the branches so that there aren't branches of branches.
        new_branches = []
        for branch in branches:
            branch = branch.optimise(info)
            if isinstance(branch, _Branch):
                new_branches.extend(branch.branches)
            else:
                new_branches.append(branch)
        return new_branches
    @staticmethod
    def _split_common_prefix(branches):
        # Common leading items can be moved out of the branches.
        prefix = []
        while True:
            item = branches[0].get_first()
            if not item:
                break
            if any(branch.get_first() != item for branch in branches[1 : ]):
                break
            prefix.append(item)
            branches = [branch.drop_first() for branch in branches]
        return prefix, branches
    @staticmethod
    def _split_common_suffix(branches):
        # Common trailing items can be moved out of the branches.
        suffix = []
        while True:
            item = branches[0].get_last()
            if not item:
                break
            if any(branch.get_last() != item for branch in branches[1 : ]):
                break
            suffix.append(item)
            branches = [branch.drop_last() for branch in branches]
        return list(reversed(suffix)), branches
    @staticmethod
    def _merge_character_prefixes(info, branches):
        # Branches with the same character prefix can be grouped together if
        # they are separated only by other branches with a character prefix.
        char_type = None
        char_prefixes = defaultdict(list)
        order = {}
        new_branches = []
        for branch in branches:
            first = branch.get_first()
            if isinstance(first, _Character) and first.positive:
                if type(first) is not char_type:
                    if char_prefixes:
                        _Branch._flush_char_prefix(info, char_type,
                          char_prefixes, order, new_branches)
                        char_prefixes.clear()
                        order.clear()
                    char_type = type(first)
                char_prefixes[first.value].append(branch)
                order.setdefault(first.value, len(order))
            else:
                if char_prefixes:
                    _Branch._flush_char_prefix(info, char_type, char_prefixes,
                      order, new_branches)
                    char_prefixes.clear()
                    order.clear()
                char_type = None
                new_branches.append(branch)
        if char_prefixes:
            _Branch._flush_char_prefix(info, char_type, char_prefixes, order,
              new_branches)
        return new_branches
    @staticmethod
    def _reduce_to_set(info, branches):
        # Can the branches be reduced to a set?
        new_branches = []
        members = []
        for branch in branches:
            t = type(branch)
            if t is _Character and branch.positive:
                members.append(branch)
            elif isinstance(branch, _Property):
                members.append(branch)
            elif t is _SetUnion and branch.positive:
                for i in branch.items:
                    if isinstance(i, (_Character, _Property)):
                        members.append(i)
                    else:
                        _Branch._flush_set_members(info, members, new_branches)
            else:
                _Branch._flush_set_members(info, members, new_branches)
                members = []
                new_branches.append(branch)
        _Branch._flush_set_members(info, members, new_branches)
        return new_branches
    @staticmethod
    def _flush_char_prefix(info, char_type, prefixed, order, new_branches):
        for value, branches in sorted(prefixed.items(), key=lambda pair:
          order[pair[0]]):
            if len(branches) == 1:
                new_branches.extend(branches)
            else:
                subbranches = []
                optional = False
                for branch in branches:
                    b = branch.drop_first()
                    if b:
                        subbranches.append(b)
                    elif not optional:
                        subbranches.append(_Sequence())
                        optional = True
                sequence = _Sequence([char_type(value), _Branch(subbranches)])
                new_branches.append(sequence.optimise(info))
    @staticmethod
    def _flush_set_members(info, members, new_branches):
        if members:
            new_branches.append(_SetUnion(members).optimise(info))

class _Character(_RegexBase):
    _opcode = {False: _OP.CHARACTER, True: _OP.CHARACTER_REV}
    _op_name = {False: "CHARACTER", True: "CHARACTER_REV"}
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    def __init__(self, ch, positive=True, zerowidth=False):
        self.value, self.positive, self.zerowidth = ch, bool(positive), \
          bool(zerowidth)
        self._key = self.__class__, self.value, self.positive, self.zerowidth
    def compile(self, reverse=False):
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        return [(self._opcode[reverse], flags, self.value)]
    def dump(self, indent=0, reverse=False):
        print("{}{} {} {}".format(_INDENT * indent, self._op_name[reverse],
          self._pos_text[self.positive], self.value))
    def firstset(self):
        try:
            return set([self])
        except TypeError:
            print("_key of character is {}".format(repr(self._key)))
            print("Hash value is {}".format(hash(self._key)))
            raise
    def has_simple_start(self):
        return True
    def is_case_sensitive(self, info):
        char_type = info.char_type
        return char_type(self.value).lower() != char_type(self.value).upper()

class _CharacterIgn(_Character):
    _opcode = {False: _OP.CHARACTER_IGN, True: _OP.CHARACTER_IGN_REV}
    _op_name = {False: "CHARACTER_IGN", True: "CHARACTER_IGN_REV"}
    def __init__(self, ch, positive=True, zerowidth=False):
        self.value, self.positive, self.zerowidth = ch, bool(positive), \
          bool(zerowidth)
        self._key = self.__class__, self.value, self.positive, self.zerowidth
        self._optimised = False
    def optimise(self, info):
        if self._optimised:
            return self
        # Case-sensitive matches are faster, so convert to a case-sensitive
        # instance if the character is case-insensitive.
        if self.is_case_sensitive(info):
            self._optimised = True
            return self
        return _Character(self.value, positive=self.positive,
          zerowidth=self.zerowidth)

class _Conditional(_StructureBase):
    def __init__(self, info, group, yes_item, no_item):
        self.info, self.group, self.yes_item, self.no_item = info, group, \
          yes_item, no_item
        self._optimised = False
    def fix_groups(self):
        try:
            self.group = int(self.group)
        except ValueError:
            try:
                self.group = self.info.group_index[self.group]
            except KeyError:
                raise error("unknown group")
        if not 1 <= self.group <= self.info.group_count:
            raise error("unknown group")
        self.yes_item.fix_groups()
        if self.no_item:
            self.no_item.fix_groups()
        else:
            self.no_item = _Sequence()
    def optimise(self, info):
        if self._optimised:
            return self
        if self.yes_item.is_empty() and self.no_item.is_empty():
            return _Sequence()
        self.yes_item = self.yes_item.optimise(info)
        self.no_item = self.no_item.optimise(info)
        self._optimised = True
        return self
    def pack_characters(self):
        self.yes_item = self.yes_item.pack_characters()
        self.no_item = self.no_item.pack_characters()
        return self
    def is_empty(self):
        return self.yes_item.is_empty() and self.no_item.is_empty()
    def is_atomic(self):
        return self.yes_item.is_atomic() and self.no_item.is_atomic()
    def contains_group(self):
        return self.yes_item.contains_group() or self.no_item.contains_group()
    def compile(self, reverse=False):
        code = [(_OP.GROUP_EXISTS, self.group)]
        code.extend(self.yes_item.compile(reverse))
        add_code = self.no_item.compile(reverse)
        if add_code:
            code.append((_OP.NEXT, ))
            code.extend(add_code)
        code.append((_OP.END, ))
        return code
    def remove_captures(self):
        self.yes_item = self.yes_item.remove_captures()
        if self.no_item:
            self.no_item = self.no_item.remove_captures()
    def dump(self, indent=0, reverse=False):
        print("{}GROUP_EXISTS {}".format(_INDENT * indent, self.group))
        self.yes_item.dump(indent + 1, reverse)
        if self.no_item:
            print("{}OR".format(_INDENT * indent))
            self.no_item.dump(indent + 1, reverse)
    def firstset(self):
        return self.yes_item.firstset() | self.no_item.firstset()
    def __eq__(self, other):
        return type(self) is type(other) and (self.group, self.yes_item,
          self.no_item) == (other.group, other.yes_item, other.no_item)

class _DefaultBoundary(_ZeroWidthBase):
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    def __init__(self, positive=True):
        self.positive = bool(positive)
        self._key = self.__class__, self.positive
    def compile(self, reverse=False):
        return [(_OP.DEFAULT_BOUNDARY, int(self.positive))]
    def dump(self, indent=0, reverse=False):
        print("{}DEFAULT_BOUNDARY {}".format(_INDENT * indent,
          self._pos_text[self.positive]))

class _EndOfLine(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.END_OF_LINE, )]
    def dump(self, indent=0, reverse=False):
        print("{}END_OF_LINE".format(_INDENT * indent))

class _EndOfLineU(_EndOfLine):
    def compile(self, reverse=False):
        return [(_OP.END_OF_LINE_U, )]
    def dump(self, indent=0, reverse=False):
        print("{}END_OF_LINE_U".format(_INDENT * indent))

class _EndOfString(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.END_OF_STRING, )]
    def dump(self, indent=0, reverse=False):
        print("{}END_OF_STRING".format(_INDENT * indent))

class _EndOfStringLine(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.END_OF_STRING_LINE, )]
    def dump(self, indent=0, reverse=False):
        print("{}END_OF_STRING_LINE".format(_INDENT * indent))

class _EndOfStringLineU(_EndOfStringLine):
    def compile(self, reverse=False):
        return [(_OP.END_OF_STRING_LINE_U, )]
    def dump(self, indent=0, reverse=False):
        print("{}END_OF_STRING_LINE_U".format(_INDENT * indent))

class _Grapheme(_RegexBase):
    def __init__(self):
        self._key = self.__class__
    def compile(self, reverse=False):
        # Match at least 1 character until a grapheme boundary is reached.
        # Note that this is the same whether matching forwards or backwards.
        character_matcher = _LazyRepeat(_AnyAll(), 1, None).compile(reverse)
        boundary_matcher = [(_OP.GRAPHEME_BOUNDARY, 1)]
        return character_matcher + boundary_matcher
    def dump(self, indent=0, reverse=False):
        print("{}GRAPHEME".format(_INDENT * indent))

class _GreedyRepeat(_StructureBase):
    _opcode = _OP.GREEDY_REPEAT
    _op_name = "GREEDY_REPEAT"
    def __init__(self, subpattern, min_count, max_count):
        self.subpattern, self.min_count, self.max_count = subpattern, \
          min_count, max_count
        self._optimised = False
    def fix_groups(self):
        self.subpattern.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        subpattern = self.subpattern.optimise(info)
        if (self.min_count, self.max_count) == (1, 1) or subpattern.is_empty():
            return subpattern
        self.subpattern = subpattern
        self._optimised = True
        return self
    def pack_characters(self):
        self.subpattern = self.subpattern.pack_characters()
        return self
    def is_empty(self):
        return self.subpattern.is_empty()
    def is_atomic(self):
        return self.min_count == self.max_count and self.subpattern.is_atomic()
    def contains_group(self):
        return self.subpattern.contains_group()
    def compile(self, reverse=False):
        repeat = [self._opcode, self.min_count]
        if self.max_count is None:
            repeat.append(_UNLIMITED)
        else:
            repeat.append(self.max_count)
        return [tuple(repeat)] + self.subpattern.compile(reverse) + [(_OP.END,
          )]
    def remove_captures(self):
        self.subpattern = self.subpattern.remove_captures()
        return self
    def dump(self, indent=0, reverse=False):
        if self.max_count is None:
            print("{}{} {} INF".format(_INDENT * indent, self._op_name,
              self.min_count))
        else:
            print("{}{} {} {}".format(_INDENT * indent, self._op_name,
              self.min_count, self.max_count))
        self.subpattern.dump(indent + 1, reverse)
    def firstset(self):
        fs = self.subpattern.firstset()
        if self.min_count == 0:
            fs.add(None)
        return fs or set([None])
    def __eq__(self, other):
        return type(self) is type(other) and (self.subpattern, self.min_count,
          self.max_count) == (other.subpattern, other.min_count,
          other.max_count)

class _Group(_StructureBase):
    def __init__(self, info, group, subpattern):
        self.info, self.group, self.subpattern = info, group, subpattern
        self._optimised = False
    def fix_groups(self):
        self.subpattern.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        self.subpattern = self.subpattern.optimise(info)
        self._optimised = True
        return self
    def pack_characters(self):
        self.subpattern = self.subpattern.pack_characters()
        return self
    def is_empty(self):
        return self.subpattern.is_empty()
    def is_atomic(self):
        return self.subpattern.is_atomic()
    def contains_group(self):
        return True
    def compile(self, reverse=False):
        return [(_OP.GROUP, self.group)] + self.subpattern.compile(reverse) + \
          [(_OP.END, )]
    def remove_captures(self):
        return self.subpattern.remove_captures()
    def dump(self, indent=0, reverse=False):
        print("{}GROUP {}".format(_INDENT * indent, self.group))
        self.subpattern.dump(indent + 1, reverse)
    def firstset(self):
        return self.subpattern.firstset()
    def has_simple_start(self):
        return self.subpattern.has_simple_start()
    def __eq__(self, other):
        return type(self) is type(other) and (self.group, self.subpattern) == \
          (other.group, other.subpattern)

class _LazyRepeat(_GreedyRepeat):
    _opcode = _OP.LAZY_REPEAT
    _op_name = "LAZY_REPEAT"

class _LookAround(_StructureBase):
    _dir_text = {False: "AHEAD", True: "BEHIND"}
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    def __init__(self, behind, positive, subpattern):
        self.behind, self.positive, self.subpattern = bool(behind), \
          bool(positive), subpattern
        self._optimised = False
    def fix_groups(self):
        self.subpattern.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        subpattern = self.subpattern.optimise(info)
        if self.positive and subpattern.is_empty():
            return subpattern
        self.subpattern = subpattern
        self._optimised = True
        return self
    def pack_characters(self):
        self.subpattern = self.subpattern.pack_characters()
        return self
    def is_empty(self):
        return self.subpattern.is_empty()
    def is_atomic(self):
        return self.subpattern.is_atomic()
    def contains_group(self):
        return self.subpattern.contains_group()
    def compile(self, reverse=False):
        return [(_OP.LOOKAROUND, int(self.positive), int(not self.behind))] + \
          self.subpattern.compile(self.behind) + [(_OP.END, )]
    def dump(self, indent=0, reverse=False):
        print("{}LOOKAROUND {} {}".format(_INDENT * indent,
          self._dir_text[self.behind], self._pos_text[self.positive]))
        self.subpattern.dump(indent + 1, self.behind)
    def firstset(self):
        return set([None])
    def __eq__(self, other):
        return type(self) is type(other) and (self.behind, self.positive,
          self.subpattern) == (other.behind, other.positive, other.subpattern)
    def can_repeat(self):
        return False

class _Property(_RegexBase):
    _opcode = {False: _OP.PROPERTY, True: _OP.PROPERTY_REV}
    _op_name = {False: "PROPERTY", True: "PROPERTY_REV"}
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    def __init__(self, value, positive=True, zerowidth=False):
        self.value, self.positive, self.zerowidth = value, bool(positive), \
          bool(zerowidth)
        self._key = self.__class__, self.value, self.positive, self.zerowidth
    def compile(self, reverse=False):
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        return [(self._opcode[reverse], flags, self.value)]
    def dump(self, indent=0, reverse=False):
        print("{}{} {} {}".format(_INDENT * indent, self._op_name[reverse],
          self._pos_text[self.positive], self.value))
    def firstset(self):
        try:
            return set([self])
        except TypeError:
            print("_key of property is {}".format(self._key))
            raise
    def has_simple_start(self):
        return True
    def is_case_sensitive(self, info):
        return True

class _RefGroup(_RegexBase):
    _opcode = {False: _OP.REF_GROUP, True: _OP.REF_GROUP_REV}
    _op_name = {False: "REF_GROUP", True: "REF_GROUP_REV"}
    def __init__(self, info, group):
        self.info, self.group = info, group
        self._key = self.__class__, self.group
    def fix_groups(self):
        try:
            self.group = int(self.group)
        except ValueError:
            try:
                self.group = self.info.group_index[self.group]
            except KeyError:
                raise error("unknown group")
        if not 1 <= self.group <= self.info.group_count:
            raise error("unknown group")
        self._key = self.__class__, self.group
    def compile(self, reverse=False):
        return [(self._opcode[reverse], self.group)]
    def remove_captures(self):
        raise error("group reference not allowed")
    def dump(self, indent=0, reverse=False):
        print("{}{} {}".format(_INDENT * indent, self._op_name[reverse],
          self.group))

class _RefGroupIgn(_RefGroup):
    _opcode = {False: _OP.REF_GROUP_IGN, True: _OP.REF_GROUP_IGN_REV}
    _op_name = {False: "REF_GROUP_IGN", True: "REF_GROUP_IGN_REV"}

class _SearchAnchor(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.SEARCH_ANCHOR, )]
    def dump(self, indent=0, reverse=False):
        print("{}SEARCH_ANCHOR".format(_INDENT * indent))

class _Sequence(_StructureBase):
    def __init__(self, sequence=None):
        if sequence is None:
            sequence = []
        self.sequence = sequence
        self._optimised = False
    def fix_groups(self):
        for subpattern in self.sequence:
            subpattern.fix_groups()
    def optimise(self, info):
        if self._optimised:
            return self
        # Flatten the sequences.
        sequence = []
        for subpattern in self.sequence:
            subpattern = subpattern.optimise(info)
            if isinstance(subpattern, _Sequence):
                sequence.extend(subpattern.sequence)
            else:
                sequence.append(subpattern)
        if len(sequence) == 1:
            return sequence[0]
        self.sequence = sequence
        self._optimised = True
        return self
    def pack_characters(self):
        sequence = []
        char_type, characters = _Character, []
        for subpattern in self.sequence:
            if type(subpattern) is char_type and subpattern.positive:
                characters.append(subpattern.value)
            else:
                if characters:
                    _Sequence._flush_characters(char_type, characters, sequence)
                    characters = []
                if type(subpattern) in _all_char_types and subpattern.positive:
                    char_type = type(subpattern)
                    characters.append(subpattern.value)
                else:
                    sequence.append(subpattern.pack_characters())
        if characters:
            _Sequence._flush_characters(char_type, characters, sequence)
        if len(sequence) == 1:
            return sequence[0]
        self.sequence = sequence
        return self
    def is_empty(self):
        return all(subpattern.is_empty() for subpattern in self.sequence)
    def is_atomic(self):
        return all(subpattern.is_atomic() for subpattern in self.sequence)
    def contains_group(self):
        return any(subpattern.contains_group() for subpattern in self.sequence)
    def get_first(self):
        if self.sequence:
            return self.sequence[0]
        return None
    def drop_first(self):
        if len(self.sequence) == 2:
            return self.sequence[1]
        return _Sequence(self.sequence[1 : ])
    def get_last(self):
        if self.sequence:
            return self.sequence[-1]
        return None
    def drop_last(self):
        if len(self.sequence) == 2:
            return self.sequence[-2]
        return _Sequence(self.sequence[ : -1])
    def compile(self, reverse=False):
        if reverse:
            seq = list(reversed(self.sequence))
        else:
            seq = self.sequence
        code = []
        for subpattern in seq:
            code.extend(subpattern.compile(reverse))
        return code
    def remove_captures(self):
        self.sequence = [subpattern.remove_captures() for subpattern in
          self.sequence]
        return self
    def dump(self, indent=0, reverse=False):
        for subpattern in self.sequence:
            subpattern.dump(indent, reverse)
    def firstset(self):
        fs = set()
        for subpattern in self.sequence:
            fs = (fs - set([None])) | subpattern.firstset()
            if None not in fs:
                return fs
        return fs or set([None])
    def has_simple_start(self):
        return self.sequence and self.sequence[0].has_simple_start()
    def __eq__(self, other):
        return type(self) is type(other) and self.sequence == other.sequence
    @staticmethod
    def _flush_characters(char_type, characters, sequence):
        if not characters:
            return
        if len(characters) == 1:
            sequence.append(char_type(characters[0]))
        else:
            sequence.append(_string_classes[char_type](characters))

class _Set(_RegexBase):
    _pos_text = {False: "NON-MATCH", True: "MATCH"}
    _big_bitset_opcode = {False: _OP.BIG_BITSET, True: _OP.BIG_BITSET_REV}
    _small_bitset_opcode = {False: _OP.SMALL_BITSET, True: _OP.SMALL_BITSET_REV}
    def __init__(self, items, positive=True, zerowidth=False):
        items = tuple(items)
        self.items, self.positive, self.zerowidth = items, positive, zerowidth
        self._key = self.__class__, self.items, self.positive, self.zerowidth
        self._optimised = False
    def dump(self, indent=0, reverse=False):
        print("{}{} {}".format(_INDENT * indent, self._op_name[reverse], self._pos_text[self.positive]))
        characters, others = [], []
        for m in self.items:
            if isinstance(m, _Character):
                characters.append(m.value)
            else:
                others.append(m)

        if characters:
            characters.sort()
            c = characters[0]
            start, end = c, c - 1
            for c in characters:
                if c > end + 1:
                    if start == end:
                        print("{}CHARACTER {}".format(_INDENT * (indent + 1),
                          start))
                    else:
                        print("{}RANGE {} {}".format(_INDENT * (indent + 1),
                          start, end))
                    start = c
                end = c
            if start == end:
                print("{}CHARACTER {}".format(_INDENT * (indent + 1), start))
            else:
                print("{}RANGE {} {}".format(_INDENT * (indent + 1), start,
                  end))
        for m in others:
            m.dump(indent + 1)
    BITS_PER_INDEX = 16
    INDEXES_PER_CODE = _BITS_PER_CODE // BITS_PER_INDEX
    CODE_MASK = (1 << _BITS_PER_CODE) - 1
    CODES_PER_SUBSET = 256 // _BITS_PER_CODE
    def _make_bitset(self, characters, positive, reverse):
        code = []
        # values for big bitset are: max_char indexes... subsets...
        # values for small bitset are: top_bits bitset
        bitset_dict = defaultdict(int)
        for c in characters:
            bitset_dict[c >> 8] |= 1 << (c & 0xFF)
        if len(bitset_dict) > 1:
            # Build a big bitset.
            indexes = []
            subset_index = {}
            for top in range(max(bitset_dict.keys()) + 1):
                subset = bitset_dict.get(top, 0)
                ind = subset_index.setdefault(subset, len(subset_index))
                indexes.append(ind)
            remainder = len(indexes) % _Set.INDEXES_PER_CODE
            if remainder:
                indexes.extend([0] * (_Set.INDEXES_PER_CODE - remainder))
            data = []
            for i in range(0, len(indexes), _Set.INDEXES_PER_CODE):
                ind = 0
                for s in range(_Set.INDEXES_PER_CODE):
                    ind |= indexes[i + s] << (_Set.BITS_PER_INDEX * s)
                data.append(ind)
            for subset, ind in sorted(subset_index.items(), key=lambda pair:
              pair[1]):
                data.extend(_Set._bitset_to_codes(subset))
            flags = int(positive) + _ZEROWIDTH_OP * int(self.zerowidth)
            code.append((self._big_bitset_opcode[reverse], flags,
              max(characters)) + tuple(data))
        else:
            # Build a small bitset.
            flags = int(positive) + _ZEROWIDTH_OP * int(self.zerowidth)
            top_bits, bitset = list(bitset_dict.items())[0]
            code.append((self._small_bitset_opcode[reverse], flags, top_bits) +
              tuple(_Set._bitset_to_codes(bitset)))
        return code
    @staticmethod
    def _bitset_to_codes(bitset):
        codes = []
        for i in range(_Set.CODES_PER_SUBSET):
            codes.append(bitset & _Set.CODE_MASK)
            bitset >>= _BITS_PER_CODE
        return codes

class _SetDiff(_Set):
    _opcode = {False: _OP.SET_DIFF, True: _OP.SET_DIFF_REV}
    _op_name = {False: "SET_DIFF", True: "SET_DIFF_REV"}
    def optimise(self, info):
        if self._optimised:
            return self
        items = []
        for m in self.items:
            m = m.optimise(info)
            if isinstance(m, _SetDiff) and m.positive:
                if items:
                    items.append(m)
                else:
                    items.extend(m.items)
            elif isinstance(m, _SetUnion) and m.positive:
                if items:
                    items.extend(m.items)
                else:
                    items.append(m)
            else:
                items.append(m)
        self.items = items
        self._optimised = True

        # We can simplify if the set contains just a single member.
        if len(self.items) == 1:
            m = self.items[0]
            if isinstance(m, _Character):
                return _Character(m.value, positive=self.positive ==
                  m.positive, zerowidth=self.zerowidth)
            if isinstance(m, _Property):
                return _Property(m.value, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)
            if isinstance(m, _Set):
                return type(m)(m.items, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)

        return self
    def compile(self, reverse=False):
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        code = [(self._opcode[reverse], flags)]
        for m in self.items:
            code.extend(m.compile())
        code.append((_OP.END, ))
        return code

class _SetInter(_Set):
    _opcode = {False: _OP.SET_INTER, True: _OP.SET_INTER_REV}
    _op_name = {False: "SET_INTER", True: "SET_INTER_REV"}
    def optimise(self, info):
        if self._optimised:
            return self
        items = []
        for m in self.items:
            m = m.optimise(info)
            if isinstance(m, _SetInter) and m.positive:
                items.extend(m.items)
            else:
                items.append(m)
        self.items = items
        self._optimised = True

        # We can simplify if the set contains just a single member.
        if len(self.items) == 1:
            m = self.items[0]
            if isinstance(m, _Character):
                return _Character(m.value, positive=self.positive ==
                  m.positive, zerowidth=self.zerowidth)
            if isinstance(m, _Property):
                return _Property(m.value, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)
            if isinstance(m, _Set):
                return type(m)(m.items, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)

        return self
    def compile(self, reverse=False):
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        code = [(self._opcode[reverse], flags)]
        for m in self.items:
            code.extend(m.compile())
        code.append((_OP.END, ))
        return code

class _SetSymDiff(_Set):
    _opcode = {False: _OP.SET_SYM_DIFF, True: _OP.SET_SYM_DIFF_REV}
    _op_name = {False: "SET_SYM_DIFF", True: "SET_SYM_DIFF_REV"}
    def optimise(self, info):
        if self._optimised:
            return self
        items = []
        for m in self.items:
            m = m.optimise(info)
            if isinstance(m, _SetSymDiff) and m.positive:
                items.extend(m.items)
            else:
                items.append(m)
        self.items = items
        self._optimised = True

        # We can simplify if the set contains just a single member.
        if len(self.items) == 1:
            m = self.items[0]
            if isinstance(m, _Character):
                return _Character(m.value, positive=self.positive ==
                  m.positive, zerowidth=self.zerowidth)
            if isinstance(m, _Property):
                return _Property(m.value, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)
            if isinstance(m, _Set):
                return type(m)(m.items, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)

        return self
    def compile(self, reverse=False):
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        code = [(self._opcode[reverse], flags)]
        for m in self.items:
            code.extend(m.compile())
        code.append((_OP.END, ))
        return code

class _SetUnion(_Set):
    _opcode = {False: _OP.SET_UNION, True: _OP.SET_UNION_REV}
    _op_name = {False: "SET_UNION", True: "SET_UNION_REV"}
    def optimise(self, info):
        if self._optimised:
            return self
        items = []
        for m in self.items:
            m = m.optimise(info)
            if isinstance(m, _SetUnion) and m.positive:
                items.extend(m.items)
            else:
                items.append(m)
        self.items = items
        self._optimised = True

        # We can simplify if the set contains just a single member.
        if len(self.items) == 1:
            m = self.items[0]
            if isinstance(m, _Character):
                return _Character(m.value, positive=self.positive ==
                  m.positive, zerowidth=self.zerowidth)
            if isinstance(m, _Property):
                return _Property(m.value, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)
            if isinstance(m, _Set):
                return type(m)(m.items, positive=self.positive == m.positive,
                  zerowidth=self.zerowidth)

        return self
    def compile(self, reverse=False):
        characters, others = [], []
        for m in self.items:
            if isinstance(m, _Character):
                characters.append(m.value)
            else:
                others.append(m)

        # If there are only characters then compile to a character or bitset.
        if not others:
            return self._make_bitset(characters, self.positive, reverse)

        # Compile a compound set.
        flags = int(self.positive) + _ZEROWIDTH_OP * int(self.zerowidth)
        code = [(self._opcode[reverse], flags)]
        if characters:
            code.extend(self._make_bitset(characters, True, False))
        for m in others:
            code.extend(m.compile())
        code.append((_OP.END, ))
        return code
    def firstset(self):
        try:
            return set([self])
        except TypeError:
            print("_key of set is {}".format(self._key))
            raise
    def has_simple_start(self):
        return True

class _StartOfLine(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.START_OF_LINE, )]
    def dump(self, indent=0, reverse=False):
        print("{}START_OF_LINE".format(_INDENT * indent))

class _StartOfLineU(_StartOfLine):
    def compile(self, reverse=False):
        return [(_OP.START_OF_LINE_U, )]
    def dump(self, indent=0, reverse=False):
        print("{}START_OF_LINE_U".format(_INDENT * indent))

class _StartOfString(_ZeroWidthBase):
    def compile(self, reverse=False):
        return [(_OP.START_OF_STRING, )]
    def dump(self, indent=0, reverse=False):
        print("{}START_OF_STRING".format(_INDENT * indent))

class _String(_RegexBase):
    _opcode = {False: _OP.STRING, True: _OP.STRING_REV}
    _op_name = {False: "STRING", True: "STRING_REV"}
    def __init__(self, characters):
        self.characters = characters
        self._key = self.__class__, self.characters
    def compile(self, reverse=False):
        return [(self._opcode[reverse], len(self.characters)) +
          tuple(self.characters)]
    def dump(self, indent=0, reverse=False):
        print("{}{} {}".format(_INDENT * indent, self._op_name[reverse],
          " ".join(map(str, self.characters))))
    def firstset(self):
        return set([_Character(self.characters[0])])
    def has_simple_start(self):
        return True
    def get_first_char(self):
        raise error("internal error")
    def drop_first_char(self):
        raise error("internal error")

class _StringIgn(_String):
    _opcode = {False: _OP.STRING_IGN, True: _OP.STRING_IGN_REV}
    _op_name = {False: "STRING_IGN", True: "STRING_IGN_REV"}
    def firstset(self):
        return set([_CharacterIgn(self.characters[0])])

_all_char_types = (_Character, _CharacterIgn)
_string_classes = {_Character: _String, _CharacterIgn: _StringIgn}

_properties = _regex.get_properties()

# Character escape sequences.
_CHARACTER_ESCAPES = {
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}

# Predefined character set escape sequences.
_CHARSET_ESCAPES = {
    "d": _lookup_property(None, "DIGIT", True),
    "D": _lookup_property(None, "DIGIT", False),
    "s": _lookup_property(None, "SPACE", True),
    "S": _lookup_property(None, "SPACE", False),
    "w": _lookup_property(None, "WORD", True),
    "W": _lookup_property(None, "WORD", False),
}

# Positional escape sequences.
_POSITION_ESCAPES = {
    "A": _StartOfString(),
    "b": _Boundary(),
    "B": _Boundary(False),
    "Z": _EndOfString(),
}

# Positional escape sequences when WORD flag set.
_WORD_POSITION_ESCAPES = dict(_POSITION_ESCAPES)
_WORD_POSITION_ESCAPES.update({
    "b": _DefaultBoundary(),
    "B": _DefaultBoundary(False),
})

class _Source:
    "Scanner for the regular expression source string."
    def __init__(self, string):
        if isinstance(string, str):
            self.string = string
            self.char_type = chr
        else:
            self.string = string.decode("latin-1")
            self.char_type = lambda c: bytes([c])
        self.pos = 0
        self.ignore_space = False
        self.sep = string[ : 0]
    def get(self):
        try:
            if self.ignore_space:
                while self.string[self.pos].isspace():
                    self.pos += 1
            ch = self.string[self.pos]
            self.pos += 1
            return ch
        except IndexError:
            return self.string[ : 0]
    def match(self, substring):
        try:
            if self.ignore_space:
                while self.string[self.pos].isspace():
                    self.pos += 1
            if not self.string.startswith(substring, self.pos):
                return False
            self.pos += len(substring)
            return True
        except IndexError:
            return False
    def expect(self, substring):
        if not self.match(substring):
            raise error("missing {}".format(substring))
    def at_end(self):
        pos = self.pos
        try:
            if self.ignore_space:
                while self.string[pos].isspace():
                    pos += 1
            return pos >= len(self.string)
        except IndexError:
            return True

class _Info:
    "Info about the regular expression."
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    def __init__(self, flags=0, char_type=None):
        self.global_flags = flags & _GLOBAL_FLAGS
        self.scoped_flags = flags & _SCOPED_FLAGS
        self.all_flags = self.global_flags | self.scoped_flags
        if not (self.global_flags & NEW):
            self.global_flags = self.all_flags
        self.group_count = 0
        self.group_index = {}
        self.group_name = {}
        self.used_groups = set()
        self.group_state = {}
        self.char_type = char_type
    def new_group(self, name=None):
        group = self.group_index.get(name)
        if group is not None:
            if group in self.used_groups:
                raise error("duplicate group")
        else:
            while True:
                self.group_count += 1
                if name is None or self.group_count not in self.group_name:
                    break
            group = self.group_count
            if name:
                self.group_index[name] = group
                self.group_name[group] = name
        self.used_groups.add(group)
        self.group_state[group] = self.OPEN
        return group
    def close_group(self, group):
        self.group_state[group] = self.CLOSED
    def is_open_group(self, name):
        if name.isdigit():
            group = int(name)
        else:
            group = self.group_index.get(name)
        return self.group_state.get(group) == self.OPEN

class Scanner:
    def __init__(self, lexicon, flags=0):
        self.lexicon = lexicon

        # Combine phrases into a compound pattern.
        patterns = []
        for phrase, action in lexicon:
            # Parse the regular expression.
            source = _Source(phrase)
            info = _Info(flags, source.char_type)
            source.ignore_space = bool(info.all_flags & VERBOSE)
            parsed = _parse_pattern(source, info)
            if not source.at_end():
                raise error("trailing characters")

            # We want to forbid capture groups within each phrase.
            patterns.append(parsed.remove_captures())

        # Combine all the subpatterns into one pattern.
        info = _Info(flags)
        patterns = [_Group(info, g + 1, p) for g, p in enumerate(patterns)]
        parsed = _Branch(patterns)

        # Optimise the compound pattern.
        parsed = parsed.optimise(info)
        parsed = parsed.pack_characters()

        reverse = bool(info.global_flags & REVERSE)

        # Compile the compound pattern. The result is a list of tuples.
        code = parsed.compile(reverse) + [(_OP.SUCCESS, )]
        if parsed.has_simple_start():
            fs_code = []
        else:
            fs_code = _compile_firstset(info, parsed.firstset())
        fs_code = _flatten_code(fs_code)

        # Flatten the code into a list of ints.
        code = _flatten_code(code)

        code = fs_code + code

        # Create the PatternObject.
        #
        # Local flags like IGNORECASE affect the code generation, but aren't
        # needed by the PatternObject itself. Conversely, global flags like
        # LOCALE _don't_ affect the code generation but _are_ needed by the
        # PatternObject.
        self.scanner = _regex.compile(None, flags & _GLOBAL_FLAGS, code, {}, {})
    def scan(self, string):
        result = []
        append = result.append
        match = self.scanner.scanner(string).match
        i = 0
        while True:
            m = match()
            if not m:
                break
            j = m.end()
            if i == j:
                break
            action = self.lexicon[m.lastindex - 1][1]
            if hasattr(action, '__call__'):
                self.match = m
                action = action(self, m.group())
            if action is not None:
                append(action)
            i = j
        return result, string[i : ]
