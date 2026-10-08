"""Run the V2 primary comparison without refitting the retained GDP nowcasts."""

from pathlib import Path

from inflation_forecast_nowcast.yoy import run

print(run(Path.cwd()))
