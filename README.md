# repology-nginx

Little Python script who replace http to https on nixpkgs github repository. (using datas on https://repology.org/repository/nix_unstable/problems).

# Before

1. use pyenv and :

```pip install -r requirements.txt```

2. clone nixpkgs repository : https://github.com/NixOS/nixpkgs

# Launch

```./replace.py [nixpkgs repository path]```
