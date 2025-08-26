$Folder = "C:\Users\Public\zscaler-cert-app-store"
$Store = Join-Path -Path $Folder -ChildPath "ZscalerCAbundle.pem"
function Create-Folder {
    ### Create Folder in user home ###
    if( -Not (Test-Path -Path $Folder ) )
        {
            New-Item -ItemType directory -Path $Folder
            $FILE = Get-Item $Folder -Force
            $FILE.attributes = 'Hidden'
            Write-Output "Folder created  zscaler-cert-app-store on user's home profile"
        }else{
            Write-Output "Folder already created. Skipping"
        }
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

function New-Bundle{
    #if bundle exist alert it'll overwrite it
    if( Test-Path -Path $Store -PathType Leaf) {
        Write-Output "Certificate bundle detected. Clearing it..."
        Clear-Content $Store
    }
    Write-Output "Generating certificate bundle..."
    #getting all certs
    #making sure
    if ((Get-ChildItem -Path Cert:\LocalMachine\Root | Where-Object {$_.Subject -match "CN=Zscaler Root CA"})) {
        Write-Output 'Zscaler root found.'
        $certs=Get-ChildItem Cert: -Recurse  | Select-Object *
        #getting certificate Authorities only
        foreach($cert in $certs){
            #going over Extensions
            $ext =  $cert.Extensions
            $ca = $false
            foreach($e in $ext) {
                if ($e.CertificateAuthority -eq $true){
                    $ca = $true
                }
            }
            if ($ca){
                $line = [System.Convert]::ToBase64String($cert.RawData)
                $issuer = "# Issuer: "+$cert.IssuerName.Name+"`n"
                $subject = "# Subject: "+$cert.SubjectName.Name+"`n"
                $serial = "# Serial: "+$cert.SerialNumber+"`n"
                $thumbprint = "# Thumbprint: "+$cert.Thumbprint+"`n"
                Add-Content -NoNewline -Path $Store -Value $issuer
                Add-Content -NoNewline -Path $Store -Value $subject
                Add-Content -NoNewline -Path $Store -Value $serial
                Add-Content -NoNewline -Path $Store -Value $thumbprint
                Add-Content -NoNewline -Path $Store -Value "-----BEGIN CERTIFICATE-----`n"
                #pem is base 64 with new linex unix format every 64 characters

                for ($i = 0; $i -lt $line.Length; $i += 64)
                {
                    $length = [Math]::Min(64, $line.Length - $i)
                    $tmp = $line.SubString($i, $length)+ "`n"
                    Add-Content -NoNewline -Path $Store -Value $tmp
                }
                Add-Content -NoNewline -Path $Store -Value "-----END CERTIFICATE-----`n`n"
            }
        }
    }else{
        Write-Output 'Zscaler root certificate not found on system trusted root CA store. Please make sure ZCC is installed'
        Break
    }
}

function Convert-Cert($certname, $penname) {
    ### Convert to PEM ###
    certutil.exe -encode $certname $pemname
}

function Add-Cert-To-Git() {
    if (Get-Command "git.exe" -ErrorAction SilentlyContinue) {
        Write-Output "--> Patch git"
        git config --system http.sslbackend schannel
    }
    else {
        Write-Output "git is either not installed or not in the %PATH%.  Skipping."
    }
}

function Add-Environment-Variables {
    # Requests, PIP, NPM, Curl, Ruby. AWS
    if (-Not [System.Environment]::GetEnvironmentVariable('REQUESTS_CA_BUNDLE') ) {
        [System.Environment]::SetEnvironmentVariable("REQUESTS_CA_BUNDLE", $Store, "Machine")
        Write-Output "REQUESTS_CA_BUNDLE Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('NODE_EXTRA_CA_CERTS') ) {
        [System.Environment]::SetEnvironmentVariable("NODE_EXTRA_CA_CERTS", $Store, "Machine")
        Write-Output "NODE_EXTRA_CA_CERTS Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('SSL_CERT_FILE') ) {
        [System.Environment]::SetEnvironmentVariable("SSL_CERT_FILE", $Store, "Machine")
        Write-Output "SSL_CERT_FILE Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('AWS_CA_BUNDLE') ) {
        [System.Environment]::SetEnvironmentVariable("AWS_CA_BUNDLE", $Store, "Machine")
        Write-Output "AWS_CA_BUNDLE Environment Variable configured"
        }
    if (-Not [System.Environment]::GetEnvironmentVariable('HTTPLIB2_CA_CERTS') ) {
        [System.Environment]::SetEnvironmentVariable("HTTPLIB2_CA_CERTS", $Store, "Machine")
        Write-Output "HTTPLIB2_CA_CERTS Environment Variable configured"
        }
}

function Main {
    Create-Folder
    New-Bundle
    Set-Location $Folder
    Add-Environment-Variables
    Add-Cert-To-Git

    Write-Output "--> Program Done."
}

# Run Program
Write-Output "Windows Zscaler Cert installer v1.0"
Test-Privileges
Main
