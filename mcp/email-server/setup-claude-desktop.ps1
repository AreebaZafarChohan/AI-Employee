# Setup Claude Desktop Config for Email MCP Server
# Run this in PowerShell to add the email MCP server to Claude Desktop

$claudeDir = "$env:APPDATA\Claude"
$configPath = "$claudeDir\claude_desktop_config.json"

# Create directory if it doesn't exist
if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    Write-Host "Created Claude config directory: $claudeDir"
}

# Load existing config or create new one
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    Write-Host "Loaded existing Claude Desktop config"
} else {
    $config = @{ mcpServers = @{} }
    Write-Host "Creating new Claude Desktop config"
}

# Get email server path (absolute path to index.js)
$emailServerPath = Resolve-Path "$PSScriptRoot\src\index.js"

# Read .env file to get credentials
$envFile = "$PSScriptRoot\.env"
$envVars = @{}
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $envVars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    Write-Host "Loaded credentials from .env file"
} else {
    Write-Error ".env file not found at $envFile"
    exit 1
}

# Add email MCP server config
$config.mcpServers.'ai-employee-email' = @{
    command = "node"
    args = @($emailServerPath.Path)
    env = @{
        GMAIL_CLIENT_ID = $envVars['GMAIL_CLIENT_ID']
        GMAIL_CLIENT_SECRET = $envVars['GMAIL_CLIENT_SECRET']
        GMAIL_REFRESH_TOKEN = $envVars['GMAIL_REFRESH_TOKEN']
        GMAIL_USER = $envVars['GMAIL_USER']
        DRY_RUN = $envVars['DRY_RUN']
    }
}

# Save config
$config | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding utf8 -Force
Write-Host "Saved config to: $configPath"
Write-Host ""
Write-Host "Email MCP Server added to Claude Desktop config!"
Write-Host "Restart Claude Desktop to apply changes."
Write-Host ""
Write-Host "Config contents:"
Get-Content $configPath
