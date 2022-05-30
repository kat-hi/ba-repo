from pyparsing import LineEnd, White, Word, nums, OneOrMore, oneOf, \
    alphanums, Combine, Group, restOfLine, Optional, alphas8bit, LineStart, ZeroOrMore, Literal, alphas, Dict, hexnums, \
    Suppress

# whitespace
_white_space_chars = ''.join([key for key in White.whiteStrs if key not in ['\r', '\n']])
_white_space = White(ws=_white_space_chars)

_text_string = OneOrMore(Word(alphanums) ^ Word(alphas8bit))
_allowed_email_chars = oneOf('. ; ! # $ % & \' * + - / = ? ^ _ ` { | } ~ @ + [ ]')

hash = 'hash=' + Word(hexnums)('hash')
parents = 'parents=' + ZeroOrMore(Word(hexnums) + Suppress(_white_space))('parents')
author_email = 'author_email=' + restOfLine('author_email') + LineEnd()
author_date = 'author_date=' + restOfLine('author_date') + LineEnd()
commit_date = 'commit_date=' + restOfLine('commit_date') + LineEnd()

_git_log_status = Combine(Suppress(LineStart()) + oneOf('A D M T U X') | oneOf('C R') + Word(nums * 3))
files = ZeroOrMore(Combine(_git_log_status +
                           restOfLine)).setResultsName('files')

ENTRY = hash + parents + author_email + author_date + commit_date + files
LOGFILE = OneOrMore(Group(ENTRY)('entry'))
