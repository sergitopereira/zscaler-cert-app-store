# Forked from https://gitlab.com/daxm/zscaler-cert-installer/-/blob/main/Zscaler_Cert_Installer_for_Windows.ps1

function Create-Folder {
    ### Create Folder in user home ###
    Write-Output "--> Change directory into users' home directory. Creating hidden forlder zscaler-cert-app-store."
    New-Item -ItemType directory -Path '~\zscaler-cert-app-store'
    $FILE=Get-Item '~\zscaler-cert-app-store' -Force
    $FILE.attributes='Hidden'
}

function Remove-Cert-Files($filelist) {
    ### Cleanup ###
    Write-Output "--> Clean up temporary cert files."
    foreach ($i in $filelist) {
        Remove-Item $i
    }
}

function Test-Privileges {
    Write-Host '--> Checking for elevated permissions.'
    if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
        Write-Warning 'Insufficient permissions to run this script. Open the PowerShell console as an administrator and run this script again.'
        Write-Warning 'In Powershell issue command: powershell Start-Process powershell -Verb runAs -FilePath <path to this ps1 file>'
        Break
    }
}

function Get-Zscaler-Cert($certname, $pemname) {
    Write-Output "--> Extract Zscaler Root CA certificate from Windows cert store."
    ### Extract ZscalerRootCertificate from Cert Store ###
    $thumbprint = (Get-ChildItem -Path Cert:\LocalMachine\Root | Where-Object {$_.Subject -match "CN=Zscaler Root CA"}).Thumbprint
    $certpath = 'Cert:\LocalMachine\Root\' + $thumbprint
    $path='~\zscaler-cert-app-store\' + $certname
    Export-Certificate -Cert $certpath -FilePath $path
}

function Convert-Cert($certname, $penname) {
    ### Convert to PEM ###
    certutil.exe -encode $certname $pemname
}

function Add-Cert-To-Git($penname) {
    if (Get-Command "git.exe" -ErrorAction SilentlyContinue) {
        Write-Output "--> Add Zscaler cert to git cert store."
        Get-Content $pemname | Add-Content $(git config --get http.sslcainfo)
    }
    else {
        Write-Output "git is either not installed or not in the %PATH%.  Skipping."
    }
}

function Add-Environment-Variables($location) {
    # Requests, PIP, NPM, Curl, Ruby. AWS
    if (-Not [System.Environment]::GetEnvironmentVariable('REQUESTS_CA_BUNDLE') ) {
        [System.Environment]::SetEnvironmentVariable("REQUESTS_CA_BUNDLE", $location, "Machine")
        Write-Output "REQUESTS_CA_BUNDLE Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('NODE_EXTRA_CA_CERTS') ) {
        [System.Environment]::SetEnvironmentVariable("NODE_EXTRA_CA_CERTS", $location, "Machine")
        Write-Output "NODE_EXTRA_CA_CERTS Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('SSL_CERT_FILE') ) {
        [System.Environment]::SetEnvironmentVariable("SSL_CERT_FILE", $location, "Machine")
        Write-Output "SSL_CERT_FILE Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('AWS_CA_BUNDLE') ) {
        [System.Environment]::SetEnvironmentVariable("AWS_CA_BUNDLE", $location, "Machine")
        Write-Output "AWS_CA_BUNDLE Environment Variable configured"
        }
}

function Add-Cert-To-Python($penname) {
    if (Get-Command "python.exe" -ErrorAction SilentlyContinue) {
        $pythonstartpath = Split-Path (Get-Command "python.exe").Path -Parent

        $pythonendpath1 = '\Lib\site-packages\pip\_vendor\certifi\cacert.pem'
        $pythonendpath2 = '\Lib\site-packages\certifi\cacert.pem'

        Write-Output "--> Add Zscaler cert to python cert store."
        $pythonpath = $pythonstartpath + $pythonendpath1
        Get-Content $pemname | Add-Content $pythonpath
        $pythonpath = $pythonstartpath + $pythonendpath2
        Get-Content $pemname | Add-Content $pythonpath
    }
    else {
        Write-Output "python is either not installed or not in the %PATH%.  Skipping."
    }
}

function Main {
    $certname = 'ZscalerRootCertificate.cer'
    $pemname = 'ZscalerRootCertificate.pem'

    Create-Folder

    Get-Zscaler-Cert $certname
    Set-Location '~\zscaler-cert-app-store'
    Convert-Cert $certname $penname
    $File=Resolve-Path "ZscalerRootCertificate.pem"

    # If cert files exist do importation to 3rd party applications.
    if ((Test-Path -Path $certname -PathType Leaf) -And (Test-Path -Path $pemname -PathType Leaf)) {
        Write-Output "--> Cert extraction and conversion successful."

        Add-Cert-To-Git $penname
        Add-Cert-To-Python $penname
        Add-Environment-Variables $File

    }
    Else {
        Write-Output "--> Extracted cert files not in expected location.  Please check home directory for files named: " + $certname + " and " + $pemname + "."
    }

    Write-Output "--> Program Done."
}

# Run Program
Write-Output "Windows Zscaler Cert installer v0.2"
Test-Privileges
Main
