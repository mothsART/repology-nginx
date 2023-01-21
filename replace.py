#!/usr/bin/env python3

import argparse
import os
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

def get_html():
    r = requests.get(URL_ROOT)
    return r.text

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
            break
    return packages

def replace_nix_file(nixpkgs_path, package):
    nix_file_path = nixpkgs_path + '/' + package['path']
    nix_file_content = Path(nix_file_path).read_text(encoding="UTF-8")
    new_content = nix_file_content.replace(package['before'], package['after'])
    if new_content == nix_file_content:
        return
    with open(nix_file_path, 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    nixpkgs_path = None
    if not args.path:
        print("Error : need a nixpkgs path")
        exit(0)
    nixpkgs_path = args.path[0]
    if not os.path.exists(nixpkgs_path):
        print(f"Error : nixpkgs path '{nixpkgs_path}' didn't exists")
        exit(0)

    index_path = '%s/index.html' % DIR_DESTINATION
    
    #html_txt = get_html()
    #os.makedirs(DIR_DESTINATION, exist_ok=True)
    #with open(index_path, 'w') as f:
    #    f.write(html_txt)

    content_index = Path(index_path).read_text(encoding="UTF-8")
    packages = get_permanent_links(content_index)

    for p in packages:
        replace_nix_file(nixpkgs_path, p)
