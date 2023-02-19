#!/usr/bin/env python3

import argparse
import os
from os import listdir, makedirs
from os.path import isfile, join, exists
from pathlib import Path

import requests
from scrapy.selector import Selector

URL_ROOT = 'https://repology.org/repository/nix_unstable/problems'
DIR_DESTINATION = 'cache'

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",
        description="Replace http to https on nixpkgs github repository. (using datas on https://repology.org/repository/nix_unstable/problems)"
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version = f"{parser.prog} version 0.1.0"
    )
    parser.add_argument('path', nargs='*')
    return parser

def get_html(url):
    r = requests.get(url)
    return r.text

def retrieve_content():
    makedirs(DIR_DESTINATION, exist_ok=True)
    html_content = get_html(URL_ROOT)
    with open(join(DIR_DESTINATION, f'page-0.html'), 'w') as f:
        f.write(html_content)
    inc = 1
    url = ''
    while True:
        new_url = "https://repology.org" + Selector(text=html_content).xpath('//div[@class="btn-group"]/a[@rel="next"]/@href').get()
        if new_url == url:
            break
        url = new_url
        html_content = get_html(url)
        inc += 1
        print(new_url)
        with open(join(DIR_DESTINATION, f'page-{inc}.html'), 'w') as f:
            f.write(html_content)

def get_permanent_links(html_txt):
    packages = []
    tr_results = Selector(text=html_txt).xpath('//tr').getall()
    for tr in tr_results:
        r = Selector(text=tr).xpath('//td[@class="text-left"]').get()
        if r and r.find("is a permanent redirect to its HTTPS counterpart") != -1:
            nixpkgs_href = Selector(text=tr).xpath('//td[@class="text-center"][2]//a/@href').get()
            code_tags = Selector(text=r).xpath('//code/text()').getall()
            packages.append({
                "path": nixpkgs_href.replace("https://github.com/NixOS/nixpkgs/blob/nixos-unstable/", ""),
                "before": code_tags[0],
                "after": code_tags[1],
            })
    return packages

def replace_nix_file(nixpkgs_path, package):
    nix_file_path = nixpkgs_path + '/' + package['path']
    nix_file_content = Path(nix_file_path).read_text(encoding="UTF-8")
    new_content = nix_file_content.replace(package['before'], package['after'])
    if new_content == nix_file_content:
        if (
            package['before'][len(package['before']) - 1] == '/'
            and package['after'][len(package['after']) - 1]
        ):
            new_content = nix_file_content.replace(
                package['before'][:-1:],
                package['after'][:-1:]
            )
        else:
            return
    with open(nix_file_path, 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    nixpkgs_path = None
    if not args.path:
        print("Error : need a nixpkgs repository path")
        exit(0)
    nixpkgs_path = args.path[0]
    if not exists(nixpkgs_path):
        print(f"Error : nixpkgs repository path '{nixpkgs_path}' didn't exists")
        exit(0)

    retrieve_content()

    repology_files = [f for f in listdir(DIR_DESTINATION) if isfile(join(DIR_DESTINATION, f))]
    packages = []
    for r_file in repology_files:
        content_index = Path(join(DIR_DESTINATION, r_file)).read_text(encoding="UTF-8")
        packages += get_permanent_links(content_index)

    for p in packages:
        replace_nix_file(nixpkgs_path, p)
