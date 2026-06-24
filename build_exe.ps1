$ErrorActionPreference = "Stop"

python -m PyInstaller `
    --onefile `
    --windowed `
    --name ComponentCatalogSelector `
    --clean `
    component_train_test_selector.py

Write-Host ""
Write-Host "Built dist\ComponentCatalogSelector.exe"
Write-Host "Place FullCatalogSTEP and FullCatalogSTL beside the executable before running it."
