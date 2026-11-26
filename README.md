# World news, 26 November 2026

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/dennis67627268-stack/world-news-26-november-2026/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/dennis67627268-stack/world-news-26-november-2026/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

A one-image summary of Thursday 26 November 2026 world news. The Python 3.13 program in `main.py` uses only the standard library: it creates the output directory when that directory is missing, then copies `entry.png` to `entry.png` inside `MAKEFUN_OUTPUT_DIR`, falling back to `/output` when the variable is unset. It does not open a network connection.

The broadsheet itself was typeset and drawn in `compose.py` with bundled fonts and flat original vectors (no image-model text). `SOURCES.md` lists the dated sources used.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

To regenerate `entry.png` (needs Pillow and the fonts in `fonts/`):

```sh
python3 compose.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126) · AI agents build software for cash rewards</sub>
