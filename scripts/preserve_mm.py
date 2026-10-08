"""Keep the just-generated original monthly target as an explicit secondary table."""

import shutil
from pathlib import Path

r = Path.cwd() / "results"
shutil.copyfile(r / "inflation_scores.csv", r / "inflation_scores_mm.csv")
