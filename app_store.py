import os
import subprocess
from prettytable import PrettyTable


class UpdateCertStore(object):
    def __init__(self):
        # self.GetZscalerRoot()
        self.installed_apps = self.installed_apps()

    def installed_apps(self):
        """Method to identify installed apps """
        result = {}
        for app in ['python', 'git', 'ruby', 'curl', 'wget', 'npm', 'libreSSL']:
            resp = subprocess.run(f'{app} --version', shell=True, capture_output=True)
            if 'not found' in resp.stdout.decode('utf-8'):
                result[app] = {
                    'installed': False,
                    'version': None,
                    'zscertInstalled': False
                }
            else:
                result[app] = {
                    'installed': True,
                    'version': resp.stdout.decode('utf-8').strip(),
                    'zscertInstalled': False}

        print(result)
        return result

    def GetZscalerRoot(self):
        """Method to download Zscaler root Certificate from keychain and store it under ~/ca_certs"""
        path = os.path.expanduser("~") + '/ca_certs'
        if not os.path.exists(path):
            resp = subprocess.run('mkdir ~/ca_certs', shell=True, capture_output=True)
            print(resp)
        subprocess.run('security find-certificate -c zscaler -p >~/ca_certs/ZscalerRootCertificate.pem', shell=True,
                       capture_output=True)
        return

    def app_python(self):
        """
        pip-system-certs package patches the PIP and the requests at runtime to use certificates
        from the default system store rather than the bundled certificates CA.PIP will trust HTTPS sites that are
        trusted by your host OS. It will also trust all the direct uses of the requests library and the other packages
        that use requests

        """
        cmd = 'pip install pip_system_certs'
        resp = subprocess.run(cmd, shell=True, capture_output=True)
        print(resp)
        self.installed_apps['python'].update(zscertInstalled=True)

    def print_screen(self, cmd, response):
        """Method to print command and response"""
        print('-' * 32)
        print(cmd)
        print('-' * 32)
        print(response)

    def add_environment_variable(self, app, environment_variable):
        """MEthod to add environment varaible"""
        home = os.path.expanduser("~")
        resp = subprocess.run('echo $0', shell=True, capture_output=True)
        if 'bash' not in resp.stdout.decode('utf-8'):
            terminal = '.zshrc'
        else:
            terminal = '.bash_profile'
        cmd = f"echo export  {environment_variable}={home}/ca_certs/ZscalerRootCertificate.pem >> {home}/{terminal}"
        resp = subprocess.run(cmd, shell=True, capture_output=True)
        self.print_screen(cmd, resp)
        resp = subprocess.run(f'source {home}/.zshrc', shell=True, capture_output=True)
        self.print_screen(f'source {home}/{terminal}', resp)
        self.installed_apps[app].update(zscertInstalled=True)

    def app_git(self):
        """Method to update git ca trusted store"""
        cmd = 'git config --global http.sslcainfo ~/ca_certs/ZscalerRootCertificate.pem'
        resp = subprocess.run(cmd, shell=True, capture_output=True)
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
        home = os.path.expanduser("~")
        cmd = f"echo ca_certificate={home}/ca_certs/ZscalerRootCertificate.pem >> {home}/.wgetrc"
        resp = subprocess.run(cmd, shell=True, capture_output=True)
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
        Method to update golang ca trusted store
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
        cmd = f"cat ~/ca_certs/ZscalerRootCertificate.pem >>/private/etc/ssl/cert.pem"
        resp = subprocess.run(cmd, shell=True, capture_output=True)
        self.print_screen(cmd, resp)
        self.installed_apps['libreSSL'].update(zscertInstalled=True)

    def print_results(self):
        """Method to print results"""
        x = PrettyTable()
        x.field_names = ["APP", "INSTALLED IN OS", "Zscaler Root Certificate"]
        x.align = "l"
        for key, value in self.installed_apps.items():
            x.add_row([key, value['installed'], value['zscertInstalled']])
        print(x)
