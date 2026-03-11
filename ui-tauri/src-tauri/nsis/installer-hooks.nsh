; MCP Synapse NSIS hooks: shortcut target correctness and stale link hygiene.
; Narrow scope: Start Menu shortcut cleanup/recreate + tmp smoke install-path normalization.

!macro SYNAPSE_SET_SAFE_DEFAULT_INSTALLDIR
  !if "${INSTALLMODE}" == "perMachine"
    ${If} ${RunningX64}
      !if "${ARCH}" == "x64"
        StrCpy $INSTDIR "$PROGRAMFILES64\${PRODUCTNAME}"
      !else if "${ARCH}" == "arm64"
        StrCpy $INSTDIR "$PROGRAMFILES64\${PRODUCTNAME}"
      !else
        StrCpy $INSTDIR "$PROGRAMFILES\${PRODUCTNAME}"
      !endif
    ${Else}
      StrCpy $INSTDIR "$PROGRAMFILES\${PRODUCTNAME}"
    ${EndIf}
  !else
    StrCpy $INSTDIR "$LOCALAPPDATA\${PRODUCTNAME}"
  !endif
!macroend

!macro SYNAPSE_NORMALIZE_TMP_INSTALLDIR
  ; Never allow repo tmp probe directories as effective install root.
  ; This is enforced even if /D= is provided.
  ${StrCase} $R8 "$INSTDIR" "L"
  ${StrLoc} $R9 $R8 "c:\mcp-router\tmp_" ">"
  ${If} $R9 != ""
    !insertmacro SYNAPSE_SET_SAFE_DEFAULT_INSTALLDIR
  ${EndIf}
!macroend

!macro SYNAPSE_DELETE_STARTMENU_SHORTCUTS
  ; Delete shortcut(s) regardless of current target path to prevent stale .lnk pollution.
  !insertmacro MUI_STARTMENU_GETFOLDER Application $AppStartMenuFolder
  Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
  ${If} $AppStartMenuFolder != ""
    Delete "$SMPROGRAMS\$AppStartMenuFolder\${PRODUCTNAME}.lnk"
    RMDir "$SMPROGRAMS\$AppStartMenuFolder"
  ${EndIf}
!macroend

!macro NSIS_HOOK_ONINIT
  ; Normalize restored previous install location before the directory page.
  !insertmacro SYNAPSE_NORMALIZE_TMP_INSTALLDIR
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro SYNAPSE_NORMALIZE_TMP_INSTALLDIR
  !insertmacro SYNAPSE_DELETE_STARTMENU_SHORTCUTS
!macroend

!macro NSIS_HOOK_POSTINSTALL
  ${If} $NoShortcutMode = 1
    ; Respect explicit no-shortcut mode.
  ${Else}
    !insertmacro MUI_STARTMENU_GETFOLDER Application $AppStartMenuFolder
    !if "${STARTMENUFOLDER}" != ""
      CreateDirectory "$SMPROGRAMS\$AppStartMenuFolder"
      Delete "$SMPROGRAMS\$AppStartMenuFolder\${PRODUCTNAME}.lnk"
      CreateShortcut "$SMPROGRAMS\$AppStartMenuFolder\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "" "$INSTDIR\${MAINBINARYNAME}.exe" 0
      !insertmacro SetLnkAppUserModelId "$SMPROGRAMS\$AppStartMenuFolder\${PRODUCTNAME}.lnk"
    !else
      Delete "$SMPROGRAMS\${PRODUCTNAME}.lnk"
      CreateShortcut "$SMPROGRAMS\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe" "" "$INSTDIR\${MAINBINARYNAME}.exe" 0
      !insertmacro SetLnkAppUserModelId "$SMPROGRAMS\${PRODUCTNAME}.lnk"
    !endif
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro SYNAPSE_DELETE_STARTMENU_SHORTCUTS
!macroend
