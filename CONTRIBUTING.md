# Contributing

## Set up

```
python -m venv .venv
.venv\Scripts\activate          # or: source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests

```
python -m unittest -v
```

Tests never touch the internet: `tests/server.py` serves `tests/site/` on a
random local port, with Range support and routes that fail (`/flaky/…`) or
send slowly (`/slow/…`). Add pages or files there when a test needs them.

## Style

- Keep slow work out of the window thread: send events from `DownloadJob`.
- New options go in `JobOptions`, `Settings`, the app and the CLI together.
- Every behaviour change comes with a test.
