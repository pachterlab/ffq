# ffq
![github version](https://img.shields.io/badge/Version-0.0.2-informational)
[![pypi version](https://img.shields.io/pypi/v/ffq)](https://pypi.org/project/ffq/0.0.2/)
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

### Fetch information of an SRA run and display it in the terminal
```
ffq [SRR]
```
where `[SRR]` is the run accession.

### Fetch information of multiple SRA runs and display it in the terminal
```
ffq [SRR1] [SRR2] ...
```
where `[SRR1]` and `[SRR2]` are run accessions.

### Write SRA run information to a single JSON file
```
ffq -o [JSON_PATH] [SRRS]
```
where `[JSON_PATH]` is the path to the JSON file that will contain run
information and `[SRRS]` is a space-delimited list of one or more
run accessions.

### Write SRA run information to multiple JSON files, one file per run
```
ffq -o [OUT_DIR] --split [SRRS]
```
where `[OUT_PATH]` is the path to directory to which to write the JSON files.
Information about each run will be written to its own separate JSON file named
`[ACCESSION].json`. `[SRRS]` is a space-delimited list of one or more
run accessions.

### Fetch information of one or more SRA study (and all of their runs)
```
ffq -t SRP [SRPS]
```
where `[SRPS]` is a space-delimited list of one or more SRA study accessions. The output is a JSON-formatted string (or a JSON file if `-o` is provided) with study accessions as keys. When `--split` is also provided, each study is written to its own separate JSON.

### Fetch information of one or more GEO study (and all of their runs)
```
ffq -t GSE [GSES]
```
where `[GSES]` is a space-delimited list of one or more GEO study accessions. The output is a JSON-formatted string (or a JSON file if `-o` is provided) with study accessions as keys. When `--split` is also provided, each study is written to its own separate JSON.

### Fetch information of all studies (and all of their runs) in one or more papers
```
ffq -t DOI [DOIS]
```
where `[DOIS]` is a space-delimited list of one or more DOIs. The output is a JSON-formatted string (or a JSON file if `-o` is provided) with SRA study accessions as keys. When `--split` is also provided, each study is written to its own separate JSON.

## Examples
Examples are available in the [examples](examples) directory.

### Downloading data
`ffq` is specifically designed to download metadata and to facilitate obtaining links to sequence files. To download raw data from the links obtained with `ffq` consider using one of these tools:
 - [`fasterq dump`](https://github.com/ncbi/sra-tools/wiki/HowTo:-fasterq-dump)
 - [`pysradb`](https://github.com/saketkc/pysradb)
