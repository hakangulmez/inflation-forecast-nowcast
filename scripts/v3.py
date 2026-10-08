"""Run the frozen publication-lag inflation protocol without acquisition."""

from pathlib import Path

from inflation_forecast_nowcast.v3 import run

if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
