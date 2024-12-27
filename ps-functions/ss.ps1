
# Add scripts directory to PATH
$env:Path += ";$HOME\scripts"

function ss {
    python "C:\Users\16145\scripts\ss.py" $args

    # wait for status code 0
    while ($LASTEXITCODE -ne 0) {
        Start-Sleep -Seconds 0.2
    }


    if ($args.Count -eq 0) {
        # get first line of output.txt
        $dir = Get-Content -Path "C:\Users\16145\scripts\output.txt" | Select-Object -First 1
        Write-Host "the output is $dir"

        # Get content from the file
        $content = Get-Content -Path "C:\Users\16145\scripts\output.txt"

        # Calculate line count, subtracting 1 if skipping the first line
        $linecount = $content.Count

        # Loop through each line (starting from index 0 for first line)
        $processedLines = @()
        for ($i = 1; $i -lt $linecount; $i++) {
            $line = $content[$i]  # Get the line at the current index
            $processedLines += $line
        }

        Set-Location $dir
        foreach ($line in $processedLines) {
            Write-Host "executing $line"
            Invoke-Expression $line
            # wait for status code 0
            while ($LASTEXITCODE -ne 0) {
                Start-Sleep -Seconds 1
            }
        }
    }
}

