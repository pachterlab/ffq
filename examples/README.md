# Examples
The following are `ffq` usage examples and their outputs.

## SRR
### A single SRR
```
ffq -o srr_single.json SRR8426358
```
Output: [srr_single.json](srr_single.json)

### Multiple SRRs
```
ffq -o srr_multiple.json SRR8426358 SRR8426359
```
Output: [srr_multiple.json](srr_multiple.json)

### Multiple SRRs with `--split`
```
ffq -o srr_split --split SRR8426358 SRR8426359
```
Output: [srr_split](srr_split)

## SRP
### A single SRP
```
ffq -t SRP -o srp_single.json SRP178136
```
Output: [srp_single.json](srp_single.json)

### Multiple SRPs
```
ffq -t SRP -o srp_multiple.json SRP178136 SRP096361
```
Output: [srp_multiple.json](srp_multiple.json)

### Multiple SRPs with `--split`
```
ffq -t SRP -o srp_split --split SRP178136 SRP096361
```
Output: [srp_split](srp_split)

## GSE
### A single GSE

### Multiple GSEs

### Multiple GSEs with `--split`

## DOI
### A single DOI
```
ffq -t DOI -o doi_single.json 10.1038/s41467-019-08831-9
```
Output: [doi_single.json](doi_single.json)

### Multiple DOIs
```
ffq -t DOI -o doi_multiple.json 10.1038/s41467-019-08831-9 10.1016/j.immuni.2019.06.027
```
Output: [doi_multiple.json](doi_multiple.json)

### Multiple DOIs with `--split`
```
ffq -t DOI -o doi_multiple.json --split 10.1038/s41467-019-08831-9 10.1016/j.immuni.2019.06.027
```
Output: [doi_split](doi_split)
