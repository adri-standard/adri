# PowerShell script to check TestPyPI for ADRI versions
# Usage: .\check_testpypi_versions.ps1

# Set TLS security protocol
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Make request to TestPyPI API
try {
    $response = Invoke-WebRequest -Uri "https://test.pypi.org/pypi/adri/json" -UseBasicParsing
    
    # Parse JSON response
    $data = $response.Content | ConvertFrom-Json
    
    # Extract versions
    $versions = $data.releases.PSObject.Properties.Name
    
    # Sort versions (newest first)
    $sortedVersions = $versions | Sort-Object -Descending
    
    # Display results
    Write-Host "Available versions on TestPyPI:"
    foreach ($version in $sortedVersions) {
        Write-Host "• $version"
    }
    
    # Check for beta versions
    $betaVersions = $sortedVersions | Where-Object { $_ -like "*b*" -and $_ -notlike "*dev*" }
    if ($betaVersions) {
        Write-Host "`nBeta versions found:"
        foreach ($version in $betaVersions) {
            Write-Host "• $version"
        }
    }
} catch {
    Write-Host "Error accessing TestPyPI: $_"
}
