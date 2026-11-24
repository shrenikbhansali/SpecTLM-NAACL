"""E5 opt-in K2–5 choices; preserve the established timing loop and defaults."""
import sys
from atlas import timing_panel

def extend_parser(parser):
    action=next(a for a in parser._actions if a.dest=='K')
    action.choices=sorted(set(action.choices)|{2,3,5})
    return parser

def main():
    if '--rebuttal-draft-k' not in sys.argv:raise ValueError('Explicit --rebuttal-draft-k required')
    sys.argv.remove('--rebuttal-draft-k');original=timing_panel.parser
    timing_panel.parser=lambda:extend_parser(original())
    timing_panel.main()
if __name__=='__main__':main()
