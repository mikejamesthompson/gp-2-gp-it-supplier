# Data on GP practice GPIT system supplier from Appointments in General Practice data

This repository contains data mapping GP practice ODS codes to their main GP IT system, updated monthly, based on the data published in the Appointments in General Practice data by NHS Digital.

The data is available in the `data/gp_suppliers.csv` file.

As the data is updated monthly, changes in system supplier can be seen in the diffs between versions.

## Updating

The data is intended to be updated monthly by GitHub Actions. However, the request to get the URL for the relevant zip file is currently blocked by CloudFlare, so data is downloaded by a semi-automated GitHub Action workflow instead.

## Prerequisites

The prerequisites are specified in the `.tool-versions` file.

- Python 3.14
- uv

## Setup

```bash
uv sync
```

This will install the dependencies specified in the `pyproject.toml` file.

## Running

```bash
uv run bin/download_gpad.py --month 2025-09
```

The code does the following:

- Finds the URL for the relevant month's zip file for the Appointments in General Practice data on the NHS Digital website
- Downloads the zip file
- Unzips the data
- Processes the data to create a mapping of GP codes to their main GP IT system
- Writes the mapping to a CSV file

The script can also be given a link direct to the zip file to download. When given, the script will skip looking for the download link on the NHS Digital website and use the provided link instead:

```bash
uv run bin/download_gpad.py --month 2025-09 --zip-file https://files.digital.nhs.uk/8F/14C367/Practice_Level_Crosstab_Sep_25.zip
```
