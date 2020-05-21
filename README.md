# ffq
![github version](https://img.shields.io/badge/Version-0.0.1-informational)
[![pypi version](https://img.shields.io/pypi/v/ffq)](https://pypi.org/project/ffq/0.0.1/)
![python versions](https://img.shields.io/pypi/pyversions/ffq)
![status](https://github.com/pachterlab/ffq/workflows/CI/badge.svg)
[![pypi downloads](https://img.shields.io/pypi/dm/ffq)](https://pypi.org/project/ffq/)
[![license](https://img.shields.io/pypi/l/ffq)](LICENSE)

Fetch run information from the European Nucleotide Archive (ENA).

## Installation

```
pip install ffq
```

## Usage

### Fetch information of a single run and display it in the terminal
```
ffq [ACCESSION]
```
where `[ACCESSION]` is the run accession.

### Fetch information of multiple runs and display it in the terminal
```
ffq [ACCESSION1] [ACCESSION2] ...
```
where `[ACCESSION1]` and `[ACCESSION2]` are run accessions.

### Write run information to a single JSON file
```
ffq -o [JSON_PATH] [ACCESSIONS]
```
where `[JSON_PATH]` is the path to the JSON file that will contain run
information and `[ACCESSIONS]` is a space-delimited list of one or more
run accessions.

### Write run information to multiple JSON files, one file per run
```
ffq -o [OUT_DIR] --split [ACCESSIONS]
```
where `[OUT_PATH]` is the path to directory to which to write the JSON files.
Information about each run will be written to its own separate JSON file named
`[ACCESSION].json`. `[ACCESSIONS]` is a space-delimited list of one or more
run accessions.
