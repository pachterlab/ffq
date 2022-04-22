
# ffq
![github version](https://img.shields.io/badge/Version-0.0.4-informational)
[![pypi version](https://img.shields.io/pypi/v/ffq)](https://pypi.org/project/ffq/0.0.4/)
![python versions](https://img.shields.io/pypi/pyversions/ffq)
![status](https://github.com/pachterlab/ffq/workflows/CI/badge.svg)
[![pypi downloads](https://img.shields.io/pypi/dm/ffq)](https://pypi.org/project/ffq/)
[![license](https://img.shields.io/pypi/l/ffq)](LICENSE)

Fetch metadata information from the following databases:
- [GEO](https://www.ncbi.nlm.nih.gov/geo/): Gene Expression Omnibus, 
- [SRA](https://www.ncbi.nlm.nih.gov/sra): Sequence Read Archive, 
- [EMBL-EBI](https://www.ebi.ac.uk/): European Molecular BIology Laboratory’s European BIoinformatics Institute, 
- [DDBJ](https://www.ddbj.nig.ac.jp/index-e.html): DNA Data Bank of Japan, 
- [NIH Biosample](https://www.ncbi.nlm.nih.gov/biosample) and 
- [ENCODE](https://www.encodeproject.org/): The Encyclopedia of DNA Elements. 

`ffq` receives an accession and returns the metadata for that accession as well as the metadata for all downstream accessions following the interconnection between GEO and SRA, EMBL-EBI, DDBJ, Biosample:


<img src="https://docs.google.com/drawings/d/e/2PACX-1vQwKI33u_qjap-QU9T_v6oZ9EHLTxryB4EIOTNodEWWVFViwhcANpTmBQU4ZrS_85PEl41W64dsifi2/pub?w=2529&amp;h=1478">

By default, ffq returns all downstream metadata down to the corresponding SRR. However, the desired depth level can be specified.

`ffq` can also skip the metadata and return the raw data download links from any available host (`FTP`, `AWS`, `GCP` or `NCBI`) for GEO and SRA ids.

## Installation
```
pip install ffq
```

## Usage

### Fetch information of an accession and display it in the terminal
```
ffq [accession]
```
where `[accession]` is either:
- an SRA/EBI/DDJ accession 
	- (`SRR`, `SRX`, `SRS` or `SRP`) 
	- (`ERR`, `ERX`, `ERS` or `ERP`) 
	- (`DRR`, `DRS`, `DRX` or `DRP`)
	
- a GEO accession (`GSE` or `GSM`)
- an ENCODE accession (`ENCSR`, `ENCSB` or `ENCSD`)
- a Bioproject accession (`CXR`)
- a Biosample accession (`SAMN`')
- a DOI

##### Examples:
```bash
$ ffq SRR9990627
#=> Returns metadata for the SRR9990627 run.

$ ffq SRX7347523
#=> Returns metadata for the experiment SRX7347523 and for its associated SRR run.

$ ffq GSE129845
#=> Returns metadata for GSE129845 and for its 5 associated GSM, SRS, SRX and SRR ids.

$ ffq DRP004583
#=> Returns metadata for the study DRP004583 and its 104 associated DRS, DRX and SRR ids.

$ ffq ENCSR998WNE
#=> Returns metadata for the ENCODE experiment ENCSR998WNE.
```

### Fetch information of multiple accessions and display it in the terminal
```
ffq [accession 1] [accession 2] ...
```
where `[accession 1]` and `[accession 2]` are accessions belonging to any of the above usage example categories.

##### Examples:
```bash
$ ffq SRR11181954 SRR11181954 SRR11181956
#=> Returns metadata for the three SRR runs.

$ ffq GSM4339769 GSM4339770 GSM4339771
#=> Returns metadata for the three GSM accessions, as well as for their corresponding downstream SRS, SRX and SRR accessions.
```

### Fetch information of an accession only down to specified level

```
ffq -l [level] [accession]
```
where `[level]` is the number of downstream accessions you want to fetch

##### Examples:
```bash
$ ffq -l 1 GSM4339769
#=> Returns metadata only for GSM4339769, and not from any downstream accession.

$ ffq -l 3 
#=> Returns metadata for GSE115469 and its downstream GSM and SRS accessions.
```
### Fetch only raw data links from the host of your choice and display it in the terminal

#### FTP host
```
ffq --ftp [accession(s)]
```
where `[accession(s)]` is either a single accession or a space-delimited list of accessions.

#### AWS host
```
ffq --aws [accession(s)]
```

#### GCP host
```
ffq --gcp [accession(s)]
```

#### NCBI host
```
ffq --ncbi [accession(s)]
```

##### Examples:

```bash
# FTP
$ ffq --ftp SRR10668798
ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_1.fastq.gz ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_2.fastq.gz 

$ ffq --ftp GSE115469
accession  filetype  filenumber  link
GSM3178782  bam  1  ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P1TLH.bam
GSM3178783  bam  1  ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P2TLH.bam
GSM3178784  bam  1  ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P3TLH.bam
GSM3178785  bam  1  ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P4TLH.bam
GSM3178786  bam  1  ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P5TLH.bam

# AWS 
$ ffq --aws SRX7347523
s3://sra-pub-src-6/SRR10668798/T84_S1_L001_R1_001.fastq.1 s3://sra-pub-src-6/SRR10668798/T84_S1_L001_R2_001.fastq.1

# GCP
$ ffq --gcp ERS3861775
gs://sra-pub-src-17/ERR3585496/4834STDY7002879.bam.1

# NCBI
$ ffq --ncbi GSM2905292
https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos2/sra-pub-run-13/SRR6425163/SRR6425163.1
```

### Write accession information to a single JSON file
```
ffq -o [JSON_PATH] [accession(s)]
```
where `[JSON_PATH]` is the path to the JSON file that will contain the information 
and `[accession(s)]` is either a single accession or a space-delimited list of accessions.

### Write accession  information to multiple JSON files, one file per accession
```
ffq -o [OUT_DIR] --split [accessions]
```
where `[OUT_DIR]` is the path to directory to which to write the JSON files and `[accessions]` is a space-delimited list of accessions.
Information about each accession will be written to its own separate JSON file named `[accession].json`. 


### Fetch information of all studies (and all of their runs) in one or more papers
```
ffq [DOIS]
```
where `[DOIS]` is a space-delimited list of one or more DOIs. The output is a JSON-formatted string (or a JSON file if `-o` is provided) with SRA study accessions as keys. When `--split` is also provided, each study is written to its own separate JSON.

## Complete output examples
Examples of complete outputs are available in the [examples](examples) directory.

## Downloading data
`ffq` is specifically designed to download metadata and to facilitate obtaining links to sequence files. To download raw data from the links obtained with `ffq` you can use [`wget`](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html#using-wget) or one of these tools: 
 - [`fasterq dump`](https://github.com/ncbi/sra-tools/wiki/HowTo:-fasterq-dump)
 - [`pysradb`](https://github.com/saketkc/pysradb)
