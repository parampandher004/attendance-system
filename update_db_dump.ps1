$containerName = "my_postgres"
$dbName = "mydb"

Write-Host "Exporting schema to init.sql..."
docker exec $containerName pg_dump -U postgres -s -d $dbName | Out-File -FilePath ./db/init.sql -Encoding ascii

Write-Host "Exporting data to seed.sql..."
docker exec $containerName pg_dump -U postgres -a -d $dbName | Out-File -FilePath ./db/seed.sql -Encoding ascii

Write-Host "Database export complete!"
