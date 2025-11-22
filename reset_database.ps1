Write-Host "Stopping containers and removing DB volume..."
docker compose down -v

Write-Host "Rebuilding and starting containers..."
docker compose up --build -d

Write-Host "Waiting for PostgreSQL to initialize..."
Start-Sleep -Seconds 10

Write-Host "Database reset complete!"