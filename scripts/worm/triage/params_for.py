"""List catalog rows (role, active, bounds, template, label) whose id matches any of the given regexes (wtriage).

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/triage/params_for.py REGEX [REGEX ...]
"""
import re
import sys

import pandas as pd

from wormemu import params

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 60)
cat = params.catalog()
pat = re.compile("|".join(sys.argv[1:]))
m = cat[cat.id.str.contains(pat)]
print(m[["id", "role", "active", "inactive_why", "label", "template", "lo", "hi", "transform", "unit"]]
      .to_string(index=False))
