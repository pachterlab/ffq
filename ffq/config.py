CROSSREF_URL = 'https://api.crossref.org/works'
ENA_URL = 'https://www.ebi.ac.uk/ena/browser/api/xml'
ENA_SEARCH_URL = 'https://www.ebi.ac.uk/ena/portal/api/search'

# NCBI entrez urls
NCBI_LINK_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi'
NCBI_SEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
NCBI_SUMMARY_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
NCBI_FETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

# TODO: replace all of the uses of these URLS to the general NCBI ones
GSE_SEARCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term='
GSE_SEARCH_TERMS = '%5bGEO%20Accession&retmax=1&retmode=json'
GSE_SUMMARY_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id='
GSE_SUMMARY_TERMS = '&retmode=json'
