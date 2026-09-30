# Data

Every file in this folder is listed in `sources.json`: where it came from, when it was retrieved,
and the SHA-256 of its bytes. Anyone can then check that they hold exactly the data the paper
used, and a test fails if a file is added, changed or removed without its entry.

```json
[
  {
    "file": "cbsl/policy-rates.csv",
    "source": "https://www.cbsl.gov.lk/...",
    "retrieved": "2026-09-30",
    "sha256": "..."
  }
]
```

To get a file's SHA-256: `python -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())" data/FILE`.

The example paper simulates its prices, so it has no data yet.
