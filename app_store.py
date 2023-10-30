import os
import pdb
import subprocess
from pathlib import Path
import plistlib
from prettytable import PrettyTable
from helpers.apps import JETBRAINS_IDE_NAMES
from os import environ
import re

KEYSTORE_PASSWORD = 'changeit'


class UpdateCertStore(object):
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.GetZscalerRoot()
        self.terminal = self._detect_terminal_profile()
        self.env_variables = self._obtain_environment_variables()
        self.installed_apps = self.build_installed_apps()

    def _obtain_environment_variables(self):
        """Method to obtain system environment variables
        return string
        """
        cmd = f"cat {self.home}/{self.terminal}"
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
        return resp

    def _detect_terminal_profile(self):

        """Method to detect OSX user terminal
        Returns string
        """
        if 'bash' in environ['SHELL']:
            terminal = '.bash_profile'
        elif 'zsh' in environ['SHELL']:
            terminal = '.zshrc'
        else:
            raise ValueError("Terminal profile not supported.")
        return terminal

    def _verify_installation(self, app):
        flag = False
        if app == 'git':
            resp = subprocess.run(f'git config --list', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
            if 'ZscalerRootCertificate' in resp:
                flag = True
        if app == 'wget':
            resp = subprocess.run(f'cat {self.home}/.wgetrc', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
            if 'ZscalerRootCertificate' in resp:
                flag = True
        if app == 'python':
            if 'REQUESTS_CA_BUNDLE' in self.env_variables:
                flag = True
        if app == 'curl':
            if 'CURL_CA_BUNDLE' in self.env_variables:
                flag = True
        if app == 'npm':
            if 'NODE_EXTRA_CA_CERTS' in self.env_variables:
                flag = True
        if app == 'ruby':
            if 'SSL_CERT_FILE' in self.env_variables:
                flag = True

        if app == 'az':
            resp = subprocess.run(f'az login', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
            if 'CERTIFICATE_VERIFY_FAILED' not in resp:
                flag = True
        return flag

    def build_installed_apps(self):
        """Method to identify installed apps """
        result = {}
        for app in ['python', 'git', 'ruby', 'curl', 'wget', 'npm', 'libreSSL', 'az']:
            resp = subprocess.run(f'{app} --version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if 'not found' in resp.stdout.decode('utf-8'):
                result[app] = {
                    'installed': False,
                    'version': None,
                    'zscertInstalled': self._verify_installation(app),
                    'meta': {}
                }
            else:
                result[app] = {
                    'installed': True,
                    'version': resp.stdout.decode('utf-8').strip(),
                    'zscertInstalled': self._verify_installation(app),
                    'meta': {}
                }

        for app in JETBRAINS_IDE_NAMES:
            vendor = 'JetBrains'
            # Android Studio is a JetBrains-type IDE, but is published by Google
            if app == 'Android Studio':
                vendor = 'Google'

            app_path = os.path.join('/', 'Applications', f'{app}.app')
            # An app's version can be found in its Info.plist file
            info_path = os.path.join(app_path, 'Contents', 'Info.plist')
            installed = os.path.exists(info_path)
            version = None
            zscertInstalled = False
            keytool_path = None
            keystore_path = None

            if installed:
                info = plistlib.loads(open(info_path, 'rb').read())
                version = info['CFBundleShortVersionString']
                # Provides the application support folder path needed to find the cert store
                path_selector = info['JVMOptions']['Properties']['idea.paths.selector']

                store_path = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', vendor,
                                          path_selector, 'ssl')
                if not os.path.exists(store_path):
                    # Acts like mkdir -p
                    Path(store_path).mkdir(parents=True, exist_ok=True)

                # Searches for keytool
                keytool_paths = list(Path(app_path).glob('**/keytool'))
                # Found keytool
                if len(keytool_paths) >= 0:
                    # Assume the first one is the one we want
                    keytool_path = keytool_paths[0]
                    keystore_path = os.path.join(store_path, 'cacerts')
                    resp = subprocess.run([
                        keytool_path,
                        '-list',
                        # Find just this root certificate.  This is the alias used when importing the cert manually via
                        # the app's settings screen
                        '-alias', 'zscaler root ca',
                        '-storepass', KEYSTORE_PASSWORD,
                        '-keystore', keystore_path
                    ], capture_output=True)
                    # If it's installed, keytool will return the fingerprint
                    zscertInstalled = 'Certificate fingerprint' in resp.stdout.decode('utf-8')

            result[app] = {
                'installed': installed,
                'version': version,
                'zscertInstalled': zscertInstalled,
                'meta': {
                    # Store these paths so we don't have to determine them again later
                    'keytool_path': keytool_path,
                    'keystore_path': keystore_path
                }
            }

        return result

    def GetZscalerRoot(self):
        """Method to download Zscaler root Certificate from keychain and store it under ~/.zscaler-cert-app-store"""
        path = os.path.expanduser("~") + '/.zscaler-cert-app-store'
        if not os.path.exists(path):
            resp = subprocess.run('mkdir ~/.zscaler-cert-app-store', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(resp)
        cert_path = f'{path}/ZscalerRootCertificate.pem'
        if not os.path.exists(cert_path):
            resp = subprocess.run(
                'security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain  >~/.zscaler-cert-app-store/ZscalerRootCertificate.pem',
                shell=True,
                capture_output=True)
            print(resp)
            resp = subprocess.run(
                'security find-certificate -a -p /Library/Keychains/System.keychain  >>~/.zscaler-cert-app-store/ZscalerRootCertificate.pem',
                shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(resp)
        return cert_path

    def app_python(self):
        """
        pip-system-certs package patches the PIP and the requests at runtime to use certificates
        from the default system store rather than the bundled certificates CA.PIP will trust HTTPS sites that are
        trusted by your host OS. It will also trust all the direct uses of the requests library and the other packages
        that use requests

        """
        cmd = 'cat ~/.zscaler-cert-app-store/ZscalerRootCertificate.pem >> $(python3 -m certifi)'
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)
        # Python Requests looks automatically for REQUESTS_CA_BUNDLE environment variable.
        self.add_environment_variable('python', 'REQUESTS_CA_BUNDLE')
        self.installed_apps['python'].update(zscertInstalled=True)

    def print_screen(self, cmd, response):
        """Method to print command and response"""
        print('-' * 32)
        print(cmd)
        print('-' * 32)
        print(response)

    def add_environment_variable(self, app, environment_variable):
        """Method to add environment variable to either bash_profile or zshrc"""

        cmd = f"cat {self.home}/{self.terminal}"
        if environment_variable not in subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8'):
            cmd = f"echo export  {environment_variable}={self.home}/.zscaler-cert-app-store/ZscalerRootCertificate.pem >> {self.home}/{self.terminal}"
            resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.print_screen(cmd, resp)
            resp = subprocess.run(f'source {self.home}/.zshrc', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.print_screen(f'source {self.home}/{self.terminal}', resp)
            self.installed_apps[app].update(zscertInstalled=True)
        else:
            self.installed_apps[app].update(zscertInstalled=False)

    def app_git(self):
        """Method to update git ca trusted store"""
        cmd = 'git config --global http.sslcainfo ~/.zscaler-cert-app-store/ZscalerRootCertificate.pem'
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)
        self.installed_apps['git'].update(zscertInstalled=True)

    def app_ruby(self):
        """
        Method to update ruby ca trusted store
        gem update --system  shows ERROR:  SSL verification error
        """
        self.add_environment_variable('ruby', 'SSL_CERT_FILE')

    def app_wget(self):
        """
        Method to Add Zscaler CA certificate to wget.
        :return:
        """
        if self.installed_apps['wget']['zscertInstalled']:
            return
        home = os.path.expanduser("~")
        cmd = f"echo ca_certificate={home}/.zscaler-cert-app-store/ZscalerRootCertificate.pem >> {home}/.wgetrc"
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)
        self.installed_apps['wget'].update(zscertInstalled=True)

    def app_npm(self):
        """
        Method to Add Zscaler CA certificate to NPM.
        :return:
        """
        self.add_environment_variable('npm', 'NODE_EXTRA_CA_CERTS')

    def app_curl(self):
        """
        Method to update curl app ca trusted store
        curl recognizes the environment variable named 'CURL_CA_BUNDLE' if it is set, and uses the given path as a path
        to a CA cert bundle.
        """
        self.add_environment_variable('curl', 'CURL_CA_BUNDLE')

    def app_libreSSL(self):
        """
         The script mus be executed as root.
         sudo su
         python zscaler-cert-app-store -l
        :return:
        """
        self.GetZscalerRoot()
        cmd = f"cat ~/.zscaler-cert-app-store/ZscalerRootCertificate.pem >>/private/etc/ssl/cert.pem"
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)
        self.installed_apps['libreSSL'].update(zscertInstalled=True)

    def app_jetbrains_ide(self, name: str):
        """
        Adds the Zscaler CA certificate to a JetBrains-type IDE
        :param name: name of the IDE
        """
        app = self.installed_apps[name]
        if app['installed'] and not app['zscertInstalled']:
            cert_path = self.GetZscalerRoot()
            cmd = [
                str(app['meta']['keytool_path']),
                '-importcert',
                '-file', cert_path,
                '-alias', 'zscaler root ca',
                '-storepass', KEYSTORE_PASSWORD,
                '-noprompt',
                '-keystore', str(app['meta']['keystore_path'])
            ]
            resp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.print_screen(' '.join(cmd), resp)
            zscertInstalled = b'Certificate was added to keystore' in resp.stderr
            app.update(zscertInstalled=zscertInstalled)

    def app_ios(self):
        """
        Script to add Zscaler root certificate in Apple IOs simulator. Script ,must be run in each Simulator
        :return:
        """
        self.GetZscalerRoot()
        cmd = f"xcrun simctl keychain booted add-root-cert  ~/.zscaler-cert-app-store/ZscalerRootCertificate.pem"
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)

    def app_az(self):
        """
        Script to add Zscaler root certificate to azure-cli
        https://docs.microsoft.com/cli/azure/use-cli-effectively#work-behind-a-proxy
        :return:
        """
        self.GetZscalerRoot()
        cmd = f"az --version"
        regex = re.compile(r"location\s\'(.*?)'")
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #self.print_screen(cmd, resp)
        py = regex.findall(resp.stdout.decode('utf-8'))[0]
        cmd = f" cat  ~/.zscaler-cert-app-store/ZscalerRootCertificate.pem  >>$({py} -m certifi)"
        resp = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.print_screen(cmd, resp)

    def print_results(self):
        """Method to print results"""
        x = PrettyTable()
        x.field_names = ["APP", "INSTALLED IN OS", "Zscaler Root Certificate"]
        x.align = "l"
        for key, value in self.installed_apps.items():
            x.add_row([key, value['installed'], value['zscertInstalled']])
        print(x)
