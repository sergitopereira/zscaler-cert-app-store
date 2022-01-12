# zscaler-cert-app-store
Adds Zscaler root certificate into different application CA stores


# usage
```bash
python zscaler-cert-app-store -h
usage: zscaler-cert-app-store [-h] [-p] [-d] [-g] [-cat] [-f] [-v]

optional arguments:
  -h, --help        show this help message and exit
  -p, --python      Add Zscaler root certificate to python
  -d, --download    Download Zscaler root certificate from s3 bucket
  -r, --ruby        Add Zscaler root certificate to Ruby
  -g, --git         Add Zscaler root certificate to git
  -v, --version     Script version
```

# Installation 
```bash
git clone https://github.com/sergitopereira/zscaler-cert-app-store.git
pip3 install -r zscaler-cert-app-store/requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```


# Requirements
python3
certifi