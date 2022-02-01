# zscaler-cert-app-store
Adds Zscaler root certificate into different application CA stores

# Installation 
```bash
git clone https://github.com/sergitopereira/zscaler-cert-app-store.git
pip3 install -r zscaler-cert-app-store/requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

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

# Requirements
```bash
if Zscaler root certificate is not downloaded via script, please download to
~/ca_certs/ZscalerRootCertificate.pem

python3
pip3
```
# Script  commands

Python: The script uses pip-system-certs package and will patch the PIP and requests in oder to 
use certificates from the default system store rather than the bundled certificates CA
```bash
  command: pip install pip_system_certs
```
git: The script  will run the following command
```bash
  command: git config --global http.sslcainfo  ~/ca_certs/ZscalerRootCertificate.pem
```
curl: will add  CURL_CA_BUNDLE environment variable depending on the user terminal
```bash
  command: echo "export CURL_CA_BUNDLE=~/ca_certs/ZscalerRootCertificate.pem" >> $HOME/.bashrc
  or
  command: echo "export CURL_CA_BUNDLE=~/ca_certs/ZscalerRootCertificate.pem" >> $HOME/.zshrc
```
wget: will tun the following command
```bash
  command: echo "ca_certificate=~/ca_certs/ZscalerRootCertificate.pem" >> $HOME/.wgetrc
```
Ruby: will add SSL_CERT_FILE environment variable depending on user bash
```bash
  command: echo "export SSL_CERT_FILE=~/ca_certs/ZscalerRootCertificate.pem" >> $HOME/.bashrc
  or
  command: echo "export SSL_CERT_FILE=~/ca_certs/ZscalerRootCertificate.pem" >> $HOME/.zshrc
```

For more information, refer to https://help.zscaler.com/zia/adding-custom-certificate-application-specific-trusted-store#edge-browser

