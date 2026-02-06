# Creating a Windows Installer for Buildable

Instructions for building an NSIS-based Windows installer for Buildable.

## Prerequisites

### 1. Install NSIS

1. Install NSIS 3.x from https://nsis.sourceforge.io/Download
2. Download and install the **Large strings** special build:
   https://nsis.sourceforge.io/Special_Builds#Large_strings
   Copy the files into your NSIS installation folder.
3. (Optional) Download the **Advanced logging** special build:
   https://nsis.sourceforge.io/Special_Builds#Advanced_logging
   If not installed, the `LogSet on` line in `setup/install.nsh` must be commented out.
4. Download and install the **nsProcess** plugin (Unicode version):
   https://nsis.sourceforge.io/NsProcess_plugin

### 2. Build Buildable from Source (using Pixi)

From the repo root:

```bash
pixi run initialize
pixi run configure-release
pixi run build-release
pixi run install-release
```

> **Note:** On Windows, the build requires VS 2022 Build Tools (MSVC v143). If you
> also have VS 2025 installed, you may need to explicitly set the compiler:
> ```bash
> pixi run configure-release \
>   -DCMAKE_C_COMPILER="C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe" \
>   -DCMAKE_CXX_COMPILER="C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe" \
>   -DCMAKE_GENERATOR_PLATFORM=""
> ```

> **Note:** If SWIG fails during configure, conda-forge's swig package on Windows
> may be missing `.swg` library files. Install SWIG via `choco install swig` and
> copy the Lib folder contents to `.pixi/envs/default/Library/bin/Lib/`.

## Generate version.nsh

The installer needs a `version.nsh` file with version defines. Generate it before
building the installer:

```cmd
cd package\WindowsInstaller
.pixi\envs\default\Library\bin\FreeCADCmd.exe --safe-mode write_version_nsh.py
```

This creates `version.nsh` with `APP_VERSION_MAJOR`, `APP_VERSION_MINOR`,
`APP_VERSION_PATCH`, and `APP_VERSION_REVISION`.

If you already have `version.nsh`, you can skip generation by passing `/DFC_SKIP_VERSION_GEN`
to makensis.

## Build the Installer

From the repo root, run:

```cmd
cd package\WindowsInstaller
"C:\Program Files (x86)\NSIS\makensis.exe" /DFC_SKIP_VERSION_GEN /DFC_TEST_BUILD "/DFILES_BUILDABLE=C:\path\to\Buildable\.pixi\envs\default\Library" Buildable-installer.nsi
```

**Parameters:**

| Flag | Description |
|------|-------------|
| `/DFILES_BUILDABLE=<path>` | Path to the installed Buildable files (the pixi Library dir) |
| `/DFC_SKIP_VERSION_GEN` | Skip auto-generating `version.nsh` (use pre-generated file) |
| `/DFC_TEST_BUILD` | Disable compression for faster builds (larger output) |
| `/DExeFile=<name>` | Custom output filename for the installer exe |

> **Bash/MSYS2 users:** Use `//D` instead of `/D` to prevent path interpretation.
> ```bash
> "C:/Program Files (x86)/NSIS/makensis.exe" //DFC_SKIP_VERSION_GEN //DFC_TEST_BUILD "//DFILES_BUILDABLE=C:\path\to\.pixi\envs\default\Library" Buildable-installer.nsi
> ```

The output installer will be created in the `package/WindowsInstaller/` directory,
named like `Buildable_1.2.0-Windows-x86_64-installer-1.exe`.

## Quick Reference (Full Pipeline)

```bash
# 1. Build
pixi run initialize
pixi run configure-release
pixi run build-release
pixi run install-release

# 2. Generate version.nsh
cd package/WindowsInstaller
../../.pixi/envs/default/Library/bin/FreeCADCmd.exe --safe-mode write_version_nsh.py

# 3. Build installer
"C:/Program Files (x86)/NSIS/makensis.exe" //DFC_SKIP_VERSION_GEN "//DFILES_BUILDABLE=C:/Users/$USER/Desktop/Buildable/.pixi/envs/default/Library" Buildable-installer.nsi
```

## Settings

Version strings and paths can be edited in `Settings.nsh`:

- `APP_VERSION_EMERGENCY` — suffix for emergency releases (e.g. `"RC1"`)
- `APP_VERSION_BUILD` — build number, increment for re-uploads of same version
- `FILES_BUILDABLE` — path to installed Buildable files
- `FILES_THUMBS` — path to thumbnailer DLL
- `FILES_DEPS` — path to MSVC redistributable DLLs (not needed for conda builds)
