from pyparsing import LineEnd, White, Word, nums, OneOrMore, oneOf, \
    alphanums, Combine, Group, restOfLine, Optional, alphas8bit, LineStart, ZeroOrMore, Literal, alphas, Dict

# whitespace
_white_space_chars = ''.join([key for key in White.whiteStrs if key not in ['\r', '\n']])
_white_space = White(ws=_white_space_chars)
date_chars = oneOf('- : ( )')

parenthesis = oneOf('( )')
comma = Literal(', ')
plus = Literal('+')

svn_log_codes = oneOf('A D M R')

_text_string = OneOrMore(Word(alphanums) ^ Word(alphas8bit))
separator_horizontal = LineStart() + '------------------------------------------------------------------------' + LineEnd()
separator_vertical = _white_space + oneOf('|') + _white_space

revision = OneOrMore(Word(alphanums).setResultsName('hash')) + separator_vertical

author = Word(alphanums).setResultsName('author')

date = separator_vertical + Combine(
    OneOrMore(OneOrMore(Word(nums)) + Optional(date_chars) + Optional(_white_space) + Optional(plus))).setResultsName(
    'datetime') + restOfLine

origin_information = parenthesis + Word('from ') + Literal('/') + OneOrMore(Word(alphanums)).setResultsName(
    'origin_branch') + Literal(':') + OneOrMore(Word(nums)).setResultsName('origin_revision') + parenthesis + LineEnd()

filepath = Combine(OneOrMore(Optional(oneOf('/ .')) + OneOrMore(Word(alphanums)))).setResultsName('filepath',
                                                                                                  listAllMatches=True)

files = ZeroOrMore(Dict(
    Group(svn_log_codes.setResultsName('svn_status', listAllMatches=True) + filepath).setResultsName('changed_files',
                                                                                                     listAllMatches=True))
                   + Optional(
    Combine(OneOrMore(Literal('(from /')) + Combine(OneOrMore(Word(alphanums))).setResultsName('origin_branch')
            + Literal(':') + Combine(OneOrMore(Word(nums))).setResultsName('origin_revision') + Literal(')'))))

changed_path = LineStart() + OneOrMore(Word(alphas) + Optional(_white_space)) + Literal(':') + LineEnd() + files

log_message = LineStart() + Combine(OneOrMore(Word(alphanums)) + restOfLine)

log_entry = OneOrMore(Group(separator_horizontal + revision + author + date + changed_path + log_message))
