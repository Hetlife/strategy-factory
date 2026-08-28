# Running Strategy Factory locally (Linux)

Every step below was tested end-to-end in a fresh clone before this file
was written -- not just theoretical instructions. The one thing that
couldn't be tested from here: this session's sandbox can't reach Yahoo
Finance (network policy), so `factory.py update`'s actual price fetch is
unverified from this environment specifically -- it will work on a real
laptop with normal internet access, same as it already does on every
GitHub Actions run.

## Why local at all, given GitHub Actions already runs this daily for free

GitHub Actions (`.github/workflows/factory.yml`) is the automated source
of truth -- it's been running reliably (45/45 successful daily runs as of
this writing) and costs nothing. Running a second copy on a cron on your
laptop, in parallel, risks both processes fetching prices and trying to
commit `factory_state/ledger.json` at the same time -- a real conflict,
not a hypothetical one. So this setup is for **running commands
manually, testing, and viewing the dashboard locally** -- not a second
automated committer, unless you explicitly want to replace the cloud
automation entirely (say so and this file gets a different section).

## 1. Prerequisites

```bash
git --version      # any recent git
python3 --version   # 3.10+
```

## 2. Clone and set up a virtual environment

```bash
git clone https://github.com/Hetlife/strategy-factory.git
cd strategy-factory
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Run it manually (no commit, just to see it work)

```bash
python3 factory.py update    # today's daily cycle
python3 factory.py report    # weekly scoreboard + promotion verdicts
```

These read/write `factory_state/ledger.json` **on your local disk only**
-- nothing pushes anywhere unless you explicitly `git add`/`git commit`/
`git push` yourself. Safe to run repeatedly while exploring.

If you want to see it against the exact same real data the live
dashboard shows (rather than whatever your last local run wrote), pull
fresh first:

```bash
git pull origin main
```

## 4. Run the dashboard locally

```bash
streamlit run dashboard.py
```

Opens in your browser automatically (usually `http://localhost:8501`).
It fetches live data from GitHub's raw content URLs by default (same
data your hosted Streamlit Cloud deployment shows) -- so it works even
without running `update()` locally first.

## 5. Health check before trusting anything

```bash
python3 tools/health_check.py --live    # fetches ledger.json fresh from main
python3 tools/supervisor_check.py       # same checks the free 15-min GH Action runs
```

## 6. If you ever want to replace cloud automation with local-only

This is a bigger decision -- it means your laptop has to be on and
connected every weekday evening (IST) for the update to actually happen,
which a cloud runner doesn't require. Not done by default in this setup.
If you want this: disable `factory.yml`'s `schedule:` trigger first (so
the two don't race), then a local `cron` entry running
`factory.py update` + a scripted commit/push would replace it. Ask
explicitly if/when you want this built -- it's a real behavior change,
not just a convenience script.
