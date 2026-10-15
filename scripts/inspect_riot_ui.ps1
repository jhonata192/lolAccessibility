Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$hwnd = [IntPtr]132256
$win = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
if ($win) {
    Write-Host "Encontrou Riot Client via Handle!"
    $btnCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
    $btns = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
    Write-Host "Botoes encontrados: $($btns.Count)"
    foreach ($b in $btns) {
        Write-Host "  Botao: '$($b.Current.Name)' | AutomationId: '$($b.Current.AutomationId)'"
    }
    $textCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Text)
    $texts = $win.FindAll([System.Windows.Automation.TreeScope]::Descendants, $textCond)
    Write-Host "Textos encontrados: $($texts.Count)"
    foreach ($t in $texts) {
        if ($t.Current.Name) { Write-Host "  Texto: '$($t.Current.Name)'" }
    }
} else {
    Write-Host "Nao foi possivel obter elemento do handle."
}
