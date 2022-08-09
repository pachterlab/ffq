

# ffq
![github version](https://img.shields.io/badge/Version-0.3.0-informational)
[![pypi version](https://img.shields.io/pypi/v/ffq)](https://pypi.org/project/ffq/0.3.0/)
![python versions](https://img.shields.io/pypi/pyversions/ffq)
![status](https://github.com/pachterlab/ffq/workflows/CI/badge.svg)
![Code Coverage](https://img.shields.io/badge/Coverage-78%25-green.svg)
[![Downloads](https://static.pepy.tech/personalized-badge/ffq?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/ffq)
[![license](https://img.shields.io/pypi/l/ffq)](LICENSE)

```diff
! NCBI is depracating .SRA file links. This may result in an empty list with `--ncbi`.
+ Have a cool use case for ffq? Submit a PR to the `Use cases` section and we'll feature it!
```

Fetch metadata information from the following databases:
- [GEO](https://www.ncbi.nlm.nih.gov/geo/): Gene Expression Omnibus, 
- [SRA](https://www.ncbi.nlm.nih.gov/sra): Sequence Read Archive, 
- [EMBL-EBI](https://www.ebi.ac.uk/): European Molecular BIology Laboratory’s European BIoinformatics Institute, 
- [DDBJ](https://www.ddbj.nig.ac.jp/index-e.html): DNA Data Bank of Japan, 
- [NIH Biosample](https://www.ncbi.nlm.nih.gov/biosample):  Biological source materials used in experimental assays, 
- [ENCODE](https://www.encodeproject.org/): The Encyclopedia of DNA Elements. 

`ffq` receives an accession and returns the metadata for that accession as well as the metadata for all downstream accessions following the connections between GEO, SRA, EMBL-EBI, DDBJ, and Biosample. If you use `ffq` in a publication, please the [cite*](#cite):

```
Gálvez-Merchán, Á., et al. (2022). Metadata retrieval from sequence databases with ffq. bioRxiv 2022.05.18.492548.
```
The manuscript is available here: https://doi.org/10.1101/2022.05.18.492548.

<img src="https://docs.google.com/drawings/d/e/2PACX-1vQwKI33u_qjap-QU9T_v6oZ9EHLTxryB4EIOTNodEWWVFViwhcANpTmBQU4ZrS_85PEl41W64dsifi2/pub?w=2529&amp;h=1478">

By default, ffq returns all downstream metadata down to the level of the SRR record. However, the desired level of resolution can be specified.

`ffq` can also skip returning the metadata, and instead return the raw data download links from any available host (`FTP`, `AWS`, `GCP` or `NCBI`) for GEO and SRA ids.

## Installation

The latest release can be installed with
```bash
pip install ffq
```

The development version can be installed with
```bash
pip install git+https://github.com/pachterlab/ffq
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
- a Biosample accession (`SAMN`)
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

$ ffq -l 3 GSE115469
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
# FTP with an SRR
$ ffq --ftp SRR10668798
[
    {
        "accession": "SRR10668798",
        "filename": "SRR10668798_1.fastq.gz",
        "filetype": "fastq",
        "filesize": 31876537192,
        "filenumber": 1,
        "md5": "bf8078b5a9cc62b0fee98059f5b87fa7",
        "urltype": "ftp",
        "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_1.fastq.gz"
    },
...

# FTP with a GSE
$ ffq --ftp GSE115469
[
    {
        "accession": "SRR7276474",
        "filename": "P1TLH.bam",
        "filetype": "bam",
        "filesize": 48545467653,
        "filenumber": 1,
        "md5": "d0fde6bf21d9f97bdf349a3d6f0a8787",
        "urltype": "ftp",
        "url": "ftp://ftp.sra.ebi.ac.uk/vol1/SRA716/SRA716608/bam/P1TLH.bam"
    },
...

# AWS with SRX
$ ffq --aws SRX7347523
[
    {
        "accession": "SRR10668798",
        "filename": "T84_S1_L001_R1_001.fastq.1",
        "filetype": "fastq",
        "filesize": null,
        "filenumber": 1,
        "md5": null,
        "urltype": "aws",
        "url": "s3://sra-pub-src-6/SRR10668798/T84_S1_L001_R1_001.fastq.1"
    },
...

# GCP with ERS
$ ffq --gcp ERS3861775
[
    {
        "accession": "ERR3585496",
        "filename": "4834STDY7002879.bam.1",
        "filetype": "bam",
        "filesize": null,
        "filenumber": 1,
        "md5": null,
        "urltype": "gcp",
        "url": "gs://sra-pub-src-17/ERR3585496/4834STDY7002879.bam.1"
    }
]

# NCBI with GSM
$ ffq --ncbi GSM2905292
[
    {
        "accession": "SRR6425163",
        "filename": "SRR6425163.1",
        "filetype": "sra",
        "filesize": null,
        "filenumber": 1,
        "md5": null,
        "urltype": "ncbi",
        "url": "https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos2/sra-pub-run-13/SRR6425163/SRR6425163.1"
    }
]
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
`ffq` is specifically designed to download metadata and to facilitate obtaining links to sequence files. To download raw data from the links obtained with `ffq` you can use one of the following:
 - [`cURL`](https://curl.se/) and [`wget`](https://www.gnu.org/software/wget/) for FTP links,
 - [`aws`](https://aws.amazon.com/cli/) for AWS links,
 - [`gsutil`](https://cloud.google.com/storage/docs/gsutil_install) for GCP links,
 - [`fasterq dump`](https://github.com/ncbi/sra-tools/wiki/HowTo:-fasterq-dump) for converting SRA files to FASTQ files.


#### FTP
By default, [`cURL`](https://curl.se/) is installed on most computers and can be used to download files with FTP links. Alternatively, [`wget`](https://ena-docs.readthedocs.io/en/latest/retrieval/file-download.html#using-wget) can be used.

```bash
# Obtain FTP links
$ ffq --ftp SRR10668798
[
    {
        "accession": "SRR10668798",
        "filename": "SRR10668798_1.fastq.gz",
        "filetype": "fastq",
        "filesize": 31876537192,
        "filenumber": 1,
        "md5": "bf8078b5a9cc62b0fee98059f5b87fa7",
        "urltype": "ftp",
        "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_1.fastq.gz"
    },
    {
        "accession": "SRR10668798",
        "filename": "SRR10668798_2.fastq.gz",
        "filetype": "fastq",
        "filesize": 43760586944,
        "filenumber": 2,
        "md5": "351df47dca211c1f66ef327e280bd4fd",
        "urltype": "ftp",
        "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_2.fastq.gz"
    }
]

# Download the files one-by-one
$ curl -O ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_1.fastq.gz 
$ curl -O ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR106/098/SRR10668798/SRR10668798_2.fastq.gz 
```

Alternatively, the `url`s can be extracted from the json output with [`jq`](https://stedolan.github.io/jq/) and then piped into [`cURL`](https://curl.se/).

```bash
$ ffq --ftp SRR10668798 | jq -r '.[] | .url' | xargs curl -O
```

If you don't have `jq` installed, you can use the default program [`grep`](https://linux.die.net/man/1/grep).
```bash
$ ffq --ftp SRR10668798 | grep -Eo '"url": "[^"]*"' | grep -o '"[^"]*"$' | xargs curl -O
```

#### AWS
In order to download files from AWS, the [`aws`](https://aws.amazon.com/cli/) tool must be installed and [credentials must be setup](https://www.ncbi.nlm.nih.gov/sra/docs/sra-aws-download/).

```bash
# Pipe AWS links to aws s3 cp and download
$ ffq --aws SRX7347523 | jq -r '.[] | .url' | xargs -I {} aws s3 cp {} .
```

#### GCP
In order to download files from GCP, the [`gsutil`](https://cloud.google.com/storage/docs/gsutil_install) tool must be install and [credentials must be setup](https://www.ncbi.nlm.nih.gov/sra/docs/SRA-Google-Cloud/).

```bash
# Pipe GCP links to gsutil cp and download
$ ffq --gcp ERS3861775 | jq -r '.[] | .url' | xargs -I {} gsutil cp {} .
```

#### NCBI-SRA
SRA files downloaded from NCBI can be converted to FASTQ files using [`fastq-dump`](https://github.com/ncbi/sra-tools/tree/master/tools/fastq-dump) or the improved [`fasterq-dump`](https://github.com/ncbi/sra-tools/tree/master/tools/fasterq-dump) both of which are installed as part of [SRA Toolkit](https://github.com/ncbi/sra-tools/wiki/HowTo:-fasterq-dump).

```bash
# Pipe SRA link to curl and download the SRA file
$ ffq --ncbi GSM2905292 | jq -r '.[] | .url' | xargs curl -O

# Convert the SRA file to FASTQ files with one of the following
$ fastq-dump   ./SRR6425163.1 --split-files --include-technical -O ./SRR6425163 --gzip 
$ fasterq-dump ./SRR6425163.1 --split-files --include-technical -O ./SRR6425163        # fasterq-dump does not have gzip option
```

## Use cases
`ffq` facilitates the acquisition of publicly available sequencing data to help answer relevant research questions. 

```bash
# Goal: quantify publicly available scRNAseq data
$ pip install kb-python gget ffq
$ kb ref -i index.idx -g t2g.txt -f1 transcriptome.fa $(gget ref --ftp -w dna,gtf homo_sapiens)
$ kb count -i index.idx -g t2g.txt -x 10xv3 -o out $(ffq --ftp SRR10668798 | jq -r '.[] | .url' | tr '\n' ' ')
# -> count matrix in out/ folder

# Goal: count the total number of reads
$ ffq SRR10668798 | jq '.. | ."ENA-SPOT-COUNT"? | select(. != null)' |  paste -sd+ - | bc
624886427

# Goal: check the total size of the FASTQ files
$ ffq --ftp SRR10668798 | jq '.[] | .filesize ' blah | paste -sd+ - | bc | numfmt --to=iec-i --suffix=B
71GiB

# Goal: count the number of FASTQ files
$ ffq --ftp SRR10668798 | jq -r 'length'
2

# Goal: get sequence stats for the first 100 entries with seqkit
$ curl -s $(ffq --ftp SRR10668798 | jq -r '.[0] | .url') | zcat | head -400 | seqkit stats -a
file  format  type  num_seqs  sum_len  min_len  avg_len  max_len  Q1  Q2  Q3  sum_gap  N50  Q20(%)  Q30(%)
-     FASTQ   DNA        100    2,600       26       26       26  13  26  13        0   26   95.31   92.92
```
Submitted by [@sbooeshaghi](https://github.com/sbooeshaghi/).


```bash
# Goal: print the first 3 sequences of read 1 to the screen
$ curl -s $(ffq --ftp SRR10668798 | jq -r '.[0] | .url') | zcat | awk '(NR-2)%4==0' | head -n
NCCAAATAGGAATTACATACACCCCC
NAACCTGAGTAGATGTGTTGTTAACT
NGATCTGAGAACTCGGAACTATTTTC

# Goal: get number of counts per unique read sequence from the first 10000 reads
$ curl -s $(ffq --ftp accession | jq -r '.[0] | .url') | zcat | awk '(NR-2)%4==0'| head -n 10000 | sort | uniq -c | sort -r
4 TACACGACACTTAACGATCGGCCTTC
4 GTACTTTAGGCCCGTTTGTGTGCGAT
4 GACGGCTAGTACATGATATAACAAGC
...
```
Submitted by [@agalvezm](https://github.com/agalvezm/).


Do you have a cool use case for `ffq`? Submit a PR (including the goal, code snippet, and your username) so that we can feature it here.

## Failure modes
Many factors, independent of `ffq`, may result in failure to fetch metadata or missing metadata including:

1. broken internet connection 
2. improperly formatted accession
3. recently submitted data to SRA (not synced with ENA)
4. exceeded request rate for servers
5. missing metadata from online database

If you believe you have identified a bug in `ffq` please see the section on [contributing*](#contributing).

## Contributing
Thank you for wanting to improve `ffq`! If you have a bug that is related to `ffq` please create an issue. The issue should contain

1. the `ffq` command ran with `--verbose`,
2. the error message, and
3. the `ffq` and `python` version.

Please make all Pull Requests against the `devel` branch and include a message detailing the exact changes made, the reasons for the change, and tests that check for the correctness of those changes.

Some tips for improving the `ffq` code base:

- the developer dependencies can be installed with `pip install -r dev-requirements.txt`
- unit tests can be added to the `./tests/test_*.py`
- code reformatting can be performed by running `black ffq/`
- code quality can be checked by running `make check`
- tests can be performed by running `make test`

## Caveats and limitations
`ffq` relies on the information provided by the different APIs it uses to retrieve metadata (hosted by ENA, NCBI, ENCODE, etc). Therefore, returning consistent and accurate metadata is dependent on the accuracy and consistency of such databases. Unfortunately, we have observed instances where some APIs are updated without notice. This leads to unconsistent metadata retrieval by ffq that cannot be solved on our end.

For example, as of May 29th, the command:
```bash
ffq --ncbi SRR6835844
```
returned:
```bash
[{'accession': 'SRR6835844',
'filename': 'SRR6835844.1',
'filenumber': 1,
'filesize': None,
'filetype': 'sra',
 'md5': None,
'url': 'https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos2/sra-pub-run-13/SRR6835844/SRR6835844.1',
'urltype': 'ncbi'}]
```

On June 1st, we detected an error in one of ffq’s tests. Running the same command led to the following output:

```json
[]
```

Investigating this issue, we discovered that the output of the eutil’s efetch tool had changed (for a comparison, compare files `SRR6835844_altlinks_old.txt` and `SRR6835844_altlinks_new.txt` contained in `tests/fixtures`). In the new output, ncbi hosted links were no longer provided. This affects a large number of accessions, not only SRR6835844. We have updated our tests accordingly and will continue to monitor the situation.

## Naming
`ffq` is short for FetchFastQ.

# Cite
```
@article{galvez2022metadata,
  title={Metadata retrieval from sequence databases with ffq},
  author={G{\'a}lvez-Merch{\'a}n, {\'A}ngel and Min, Kyung Hoi Joseph and Pachter, Lior and Booeshaghi, A. Sina},
  year={2022}
}
```
