# local/

Personal setup for running this fork from a working folder, with everything
private kept *outside* the repo:

```
Costco/                 <- base folder (the repo's parent; override with COSTCO_BASE)
  .venv/                   Python 3.13 venv with this repo installed editable
  data/                    costco.db, browser profile, logs  (never in git)
  costco -> costco-cli/local/costco
  costco-cli/              this repo
```

- `setup.sh` — one-time: builds `../.venv`, installs the repo with dev extras, creates `../data`, links `../costco`.
- `costco` — launcher: sets `COSTCO_CLI_HOME` to `../data` and uses Brave as the browser (override with `COSTCO_CLI_CHROME`).
- `costco-search.html` — open in a browser and drop `data/costco.db` on it to search purchases. Runs entirely in the page; nothing is uploaded.
