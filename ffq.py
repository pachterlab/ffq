#!/usr/bin/env python3

import sys
import argparse
import requests
from bs4 import BeautifulSoup

def _check_args(args):
    if args.SRR[0:3] != "SRR":
        return False
    if len(args.SRR) != 10:
        return False
    return True

def _get_page(url):
    page = requests.get(url)
    return page

def _parse_page(page):
    soup = BeautifulSoup(page.text, "xml")
    db = soup.find_all("DB")
    for en, e in enumerate(db):
        if e.text == "ENA-FASTQ-FILES":
            idx = en
    link = soup.find_all("ID")[idx].text
    return link

def main(args):
    if not _check_args(args): return -1
    base_url = "https://www.ebi.ac.uk/ena/browser/api/xml/"
    url = base_url + args.SRR

    page = _get_page(url)
    source_link = _parse_page(page)

    page = _get_page(source_link)
    print("\t".join(page.text.split("\n")[1].split("\t")[1].split(";")))

    return 1


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=False, help="text file to store links")
    parser.add_argument("SRR")

    args = parser.parse_args()

    main(args)
