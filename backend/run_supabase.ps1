# Run Chef Bot with Supabase integration
Write-Host "Starting Chef Bot with Supabase integration..." -ForegroundColor Green

# Check if the environment variables are set
if (-not $env:SUPABASE_URL -or -not $env:SUPABASE_KEY) {
    Write-Host "Error: SUPABASE_URL or SUPABASE_KEY environment variables are not set" -ForegroundColor Red
    Write-Host "Please set these variables before running the application" -ForegroundColor Red
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host '$env:SUPABASE_URL = "https://your-project-id.supabase.co"' -ForegroundColor Yellow
    Write-Host '$env:SUPABASE_KEY = "your-supabase-anon-key"' -ForegroundColor Yellow
    exit 1
}

# Start the application
Write-Host "Using Supabase URL: $($env:SUPABASE_URL.Substring(0, 20))..." -ForegroundColor Cyan
Write-Host "Starting server with Supabase integration..." -ForegroundColor Cyan
python -m uvicorn main_supabase:app --host 0.0.0.0 --port 8000 --reload
