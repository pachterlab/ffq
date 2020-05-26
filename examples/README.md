# Examples

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

## GEO

## DOI
