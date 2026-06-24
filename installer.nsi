; ============================================================
; AirPointer Installer Script (NSIS)
; ============================================================

!define APP_NAME      "Air Pointer"
!define APP_VERSION   "1.0.0"
!define APP_EXE       "AirPointer.exe"
!define APP_DIR       "dist\AirPointer"
!define INSTALL_DIR   "$PROGRAMFILES64\Air Pointer"
!define REG_KEY       "Software\Microsoft\Windows\CurrentVersion\Uninstall\AirPointer"

; Installer settings
Name "${APP_NAME} ${APP_VERSION}"
OutFile "AirPointerSetup.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

; Modern UI
!include "MUI2.nsh"
!define MUI_ABORTWARNING

; ---- Icon (comment these two lines if you have no icon.ico) ----
!define MUI_ICON    "assets\icon.ico"
!define MUI_UNICON  "assets\icon.ico"

; ---- Pages shown during install ----
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ---- Pages shown during uninstall ----
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ============================================================
; INSTALL SECTION
; ============================================================
Section "Main" SecMain
    SetOutPath "$INSTDIR"

    ; Copy ALL files from the dist folder
    File /r "${APP_DIR}\*.*"

    ; ---- Desktop shortcut ----
    CreateShortcut \
        "$DESKTOP\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" \
        "" \
        "$INSTDIR\${APP_EXE}" 0

    ; ---- Start Menu shortcuts ----
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut \
        "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}"
    CreateShortcut \
        "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" \
        "$INSTDIR\Uninstall.exe"

    ; ---- Write uninstaller ----
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; ---- Add/Remove Programs registry entry ----
    WriteRegStr   HKLM "${REG_KEY}" "DisplayName"     "${APP_NAME}"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"  "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "Publisher"       "Air Pointer"
    WriteRegStr   HKLM "${REG_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr   HKLM "${REG_KEY}" "UninstallString" \
                  '"$INSTDIR\Uninstall.exe"'
    WriteRegStr   HKLM "${REG_KEY}" "DisplayIcon"     \
                  "$INSTDIR\${APP_EXE}"
    WriteRegDWORD HKLM "${REG_KEY}" "NoModify"        1
    WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"        1

    ; ---- Done message ----
    MessageBox MB_OK \
        "${APP_NAME} installed successfully!$\n$\nShortcut added to Desktop and Start Menu."
SectionEnd

; ============================================================
; UNINSTALL SECTION
; ============================================================
Section "Uninstall"
    ; Remove installed files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    ; Remove registry
    DeleteRegKey HKLM "${REG_KEY}"

    MessageBox MB_OK "${APP_NAME} has been successfully uninstalled."
SectionEnd