CROSSREF_URL = 'https://api.crossref.org/works'
ENA_URL = 'https://www.ebi.ac.uk/ena/browser/api/xml'
ENA_SEARCH_URL = 'https://www.ebi.ac.uk/ena/portal/api/search'
ENA_FETCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

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

# GEO entrez ftp links
FTP_GEO_URL = 'ftp.ncbi.nlm.nih.gov'
FTP_GEO_SAMPLE = '/geo/samples/'
FTP_GEO_SERIES = '/geo/series/'
FTP_GEO_SUPPL = '/suppl/'

# ENCODE REST API links
ENCODE_BIOSAMPLE_URL = 'https://www.encodeproject.org/biosamples/'
ENCODE_JSON = '/?format=json'
