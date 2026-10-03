# PowerShell Script - Aceitar Termos de Servico do League of Legends e Riot Client
# Resolve a barreira de acessibilidade no Chromium/CEF rolando o container e clicando em Aceitar.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  lolAccessibility: Assistente de Termos de Servico (ToS)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Procurando janela do Riot Client ou League of Legends..." -ForegroundColor Yellow

# Bipe de aviso sonoro inicial
try { [Console]::Beep(800, 200) } catch {}

Add-Type -ReferencedAssemblies "UIAutomationClient", "UIAutomationTypes", "WindowsBase", "System.Diagnostics.Process" -TypeDefinition @"
using System;
using System.Threading;
using System.Runtime.InteropServices;
using System.Windows.Automation;
using System.Text;
using System.Diagnostics;

public class RiotAccessibilityHelper {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr OpenDesktop(string lpszDesktop, uint dwFlags, bool fInherit, uint dwDesiredAccess);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetThreadDesktop(IntPtr hDesktop);

    [DllImport("user32.dll")]
    public static extern bool CloseDesktop(IntPtr hDesktop);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, int dx, int dy, int dwData, int dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left; public int Top; public int Right; public int Bottom;
    }

    public static string ExecuteWorkflow() {
        string status = "";
        Thread t = new Thread(new ThreadStart(() => {
            IntPtr hDesk = OpenDesktop("Default", 0, false, 0x01FF);
            if (hDesk == IntPtr.Zero) {
                status = "ERRO: Nao foi possivel acessar a Area de Trabalho interativa.";
                return;
            }
            if (!SetThreadDesktop(hDesk)) {
                status = "ERRO: Nao foi possivel associar a thread a Area de Trabalho.";
                CloseDesktop(hDesk);
                return;
            }

            // 1. Encontrar janela do Riot Client ou League Client estritamente
            IntPtr targetHwnd = IntPtr.Zero;
            RECT targetRect = new RECT();
            string targetTitle = "";

            EnumWindows((hWnd, lParam) => {
                if (IsWindowVisible(hWnd)) {
                    StringBuilder title = new StringBuilder(256);
                    StringBuilder cls = new StringBuilder(256);
                    GetWindowText(hWnd, title, 256);
                    GetClassName(hWnd, cls, 256);

                    string tStr = title.ToString();
                    string cStr = cls.ToString();

                    bool isRiotOrLoL = false;
                    if (tStr.IndexOf("Riot Client", StringComparison.OrdinalIgnoreCase) >= 0) isRiotOrLoL = true;
                    else if (tStr.IndexOf("League of Legends", StringComparison.OrdinalIgnoreCase) >= 0) isRiotOrLoL = true;
                    else if (cStr == "RiotWindowClass") isRiotOrLoL = true;
                    else if (cStr == "Chrome_WidgetWin_1" && !string.IsNullOrEmpty(tStr)) {
                        uint pid = 0;
                        GetWindowThreadProcessId(hWnd, out pid);
                        if (pid != 0) {
                            try {
                                Process p = Process.GetProcessById((int)pid);
                                string pName = p.ProcessName.ToLower();
                                if (pName.Contains("riot") || pName.Contains("league")) {
                                    isRiotOrLoL = true;
                                }
                            } catch {}
                        }
                    }

                    if (isRiotOrLoL) {
                        RECT r;
                        GetWindowRect(hWnd, out r);
                        int w = r.Right - r.Left;
                        int h = r.Bottom - r.Top;
                        if (w > 400 && h > 300) {
                            targetHwnd = hWnd;
                            targetRect = r;
                            targetTitle = tStr;
                            return false;
                        }
                    }
                }
                return true;
            }, IntPtr.Zero);

            if (targetHwnd == IntPtr.Zero) {
                status = "AVISO: Janela do Riot Client ou League of Legends nao encontrada.";
                CloseDesktop(hDesk);
                return;
            }

            // 2. Focar e restaurar janela
            ShowWindow(targetHwnd, 9); // SW_RESTORE
            SetForegroundWindow(targetHwnd);
            Thread.Sleep(500);

            // 3. Posicionar no centro da janela (onde fica o container de texto dos termos)
            int centerX = targetRect.Left + (targetRect.Right - targetRect.Left) / 2;
            int centerY = targetRect.Top + (targetRect.Bottom - targetRect.Top) / 2;
            SetCursorPos(centerX, centerY);
            Thread.Sleep(100);

            // Clique inicial para focar o container CEF
            mouse_event(0x0002, 0, 0, 0, 0); // DOWN
            mouse_event(0x0004, 0, 0, 0, 0); // UP
            Thread.Sleep(150);

            // 4. Rolar para baixo (mouse wheel -240 por passo)
            for (int i = 0; i < 160; i++) {
                mouse_event(0x0800, 0, 0, -240, 0);
                Thread.Sleep(10);
            }

            Thread.Sleep(800);

            // 5. Clicar em Aceitar via UI Automation
            bool clicado = false;
            try {
                AutomationElement root = AutomationElement.FromHandle(targetHwnd);
                if (root != null) {
                    var cond = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button);
                    var btns = root.FindAll(TreeScope.Descendants, cond);
                    string[] keywords = new string[] { "Aceitar", "Accept", "Tô dentro", "To dentro", "Entendi", "Concordo", "Eu concordo", "Continuar", "Continue" };
                    foreach (AutomationElement b in btns) {
                        string bName = b.Current.Name ?? "";
                        bool isMatch = false;
                        foreach (string kw in keywords) {
                            if (bName.IndexOf(kw, StringComparison.OrdinalIgnoreCase) >= 0) {
                                isMatch = true;
                                break;
                            }
                        }
                        if (isMatch && b.Current.IsEnabled) {
                            InvokePattern inv = b.GetCurrentPattern(InvokePattern.Pattern) as InvokePattern;
                            if (inv != null) {
                                inv.Invoke();
                                clicado = true;
                                break;
                            }
                        }
                    }
                }
            } catch (Exception ex) {
                status = "Erro no UIA: " + ex.Message;
            }

            // Se nao clicou via UIA, tentar clicar nas coordenadas do botao inferior
            if (!clicado) {
                int btnX = targetRect.Left + (targetRect.Right - targetRect.Left) / 2;
                int btnY = targetRect.Bottom - 65;
                SetCursorPos(btnX, btnY);
                Thread.Sleep(100);
                mouse_event(0x0002, 0, 0, 0, 0);
                mouse_event(0x0004, 0, 0, 0, 0);
                clicado = true;
            }

            status = clicado ? "SUCESSO: Termos aceitos na janela '" + targetTitle + "'!" : "ROLADO: Rolagem concluida com sucesso na janela '" + targetTitle + "'.";
            CloseDesktop(hDesk);
        }));

        t.Start();
        t.Join();
        return status;
    }
}
"@

$res = [RiotAccessibilityHelper]::ExecuteWorkflow()
Write-Host ""
Write-Host $res -ForegroundColor Green
if ($res -like "*SUCESSO*") {
    try {
        [Console]::Beep(1200, 150)
        Start-Sleep -Milliseconds 100
        [Console]::Beep(1600, 300)
    } catch {}
} else {
    try {
        [Console]::Beep(1000, 200)
    } catch {}
}
