import doctest
from pathlib import Path

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

paths = Path(__file__).parent.glob("*.txt")
test_suite = doctest.DocFileSuite(*paths, module_relative=False, optionflags=optionflags)
