$env:GOOGLE_CLIENT_ID = "388047669391-9ebsa7q6h35udoa3jt8vfa3jr9sr8f84.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "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"  # Replace with your actual client secret
$env:SECRET_KEY = "jK8Hs2Q9zP3tR7xY1vN5bC6aE4dF8gL0mW2nX9pZ3rT7yU6iO1"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "10080"  # 7 days
$env:PYTHONPATH = "$PWD"
$env:LOG_LEVEL = "DEBUG"

Write-Host "Starting server with enhanced logging..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
