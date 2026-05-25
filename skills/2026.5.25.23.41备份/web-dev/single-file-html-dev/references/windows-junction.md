# Windows Directory Junction for Asset Paths

## Problem
When HTML files reference assets with relative paths like `galgame_assets/covers/x.jpg`, copying the HTML into a subfolder (e.g., version archive) breaks all asset references. The browser resolves paths relative to the HTML's location, not the original location.

## Solution: NTFS Directory Junction
A junction is a Windows-native directory symlink that behaves as a real folder. It uses zero additional disk space.

### Command (run from WSL)
```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command \
  "New-Item -ItemType Junction -Path 'C:\Users\Administrator\Desktop\galgame_versions\<timestamp>\galgame_assets' -Target 'C:\Users\Administrator\Desktop\galgame_assets'"
```

### Alternatives tried and why they failed
- `ln -s` from WSL: creates Linux symlink, Windows apps don't follow it
- `cmd.exe /c mklink /J`: fails with UNC path error when cwd is WSL UNC path
- `cp -r`: works but wastes 90MB+ per version folder

### Verification
After creation, check via WSL:
```bash
search_files pattern='*' path='/mnt/c/Users/Administrator/Desktop/galgame_versions/<timestamp>/galgame_assets' target='files'
```
Should show all 46+ asset files (covers, music, bg images).

### Notes
- Junction targets must be absolute paths
- Junction source must NOT already exist
- Works for: covers, backgrounds, music, CG screenshots
- One junction per version folder, applied immediately after creating the folder
