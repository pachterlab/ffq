import sys
import requests
import utils
from bs4 import BeautifulSoup

def get_page(url):
    page = requests.get(url)
    return page
def get_soup(page):
    soup = BeautifulSoup(page.text, "xml")
    return soup

# try this: https://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=SRR8426372&result=read_run&fields=run_accession,fastq_ftp

def single(SRR):
    base_url = "https://www.ebi.ac.uk/ena/browser/api/xml/"
    url = base_url + SRR
    soup = get_soup(get_page(url))

    ftp = utils.get_ftp_links(soup)
    title = utils.get_title(soup)

    # source_link = "https://www.ebi.ac.uk/ena/data/warehouse/filereport?accession={}&result=read_run&fields=run_accession,fastq_ftp".format(SRR)

    for f in ftp:
        sys.stdout.write("{}\t{}\t{}\n".format(SRR, "\t".join(title), f))

def ffq(SRRs):
    #base = "https://www.ebi.ac.uk/ena/browser/api/xml/"
    # Looping is naive implementatino
    # xml api can take multiple SRR's as string
    for sn, s in enumerate(units):
        single(s)
    return True
