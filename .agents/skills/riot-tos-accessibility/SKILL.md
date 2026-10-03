---
name: riot-tos-accessibility
description: >-
  Resolve bloqueios de acessibilidade ao aceitar Termos de Serviço (ToS) no League of Legends
  e Riot Client quando leitores de tela (NVDA, JAWS) e comandos de teclado não conseguem rolar
  o container CEF/Chromium. Automatiza a rolagem por mouse wheel e o clique de confirmação via UI Automation.
---

# Riot Games / League of Legends ToS Accessibility Helper

## Visão Geral
Esta skill fornece instruções completas e automação para contornar a barreira de acessibilidade no cliente do League of Legends e Riot Client, especificamente no diálogo obrigatório de **Termos de Serviço**.

## O Problema de Acessibilidade
1. **Interface em CEF (Chromium Embedded Framework):** O Riot Client renderiza a interface como páginas web embutidas (`Chrome_WidgetWin_1`).
2. **Falta de listener de teclado:** A caixa de diálogo dos Termos de Serviço possui uma `div` com altura enorme (mais de 40.000 pixels) e scroll customizado que **apenas reage a eventos físicos de rolagem do mouse (`wheel`) ou arraste manual da barra**.
3. **Comportamento do leitor de telas (NVDA / JAWS):**
   - No **Modo de Navegação (Browse Mode)**, as teclas de seta apenas movem o cursor virtual do leitor de tela pelo buffer de texto sem disparar eventos de rolagem reais no Chromium.
   - No **Modo de Foco (Focus Mode)**, o leitor de telas silencia para repassar as teclas diretamente para a aplicação, mas como a Riot não implementou eventos de teclado (`Page Down`, `End`, `Arrow Down`) no container de texto, o scroll não se move e o botão **"Role para aceitar"** continua bloqueado/desabilitado.
4. **Isolamento de sessão de agentes/CLI:** Scripts de IAs ou terminais em segundo plano no Windows rodam isolados da Área de Trabalho interativa (`Default Desktop`), fazendo com que chamadas padrão de `SetCursorPos` e `mouse_event` falhem silenciosamente com `False` se a thread não for vinculada explicitamente a `WinSta0\Default`.

---

## Solução Técnica

Para resolver isso de forma confiável (seja via IA autônoma ou script do usuário):
1. **Vincular à Área de Trabalho Interativa:** Abrir a desktop interativa com `OpenDesktop("Default", ...)` e chamar `SetThreadDesktop(hDesk)` em uma nova thread limpa.
2. **Localizar e Focar a Janela do Jogo:** Buscar a janela com título `"Riot Client"` ou classe `"Chrome_WidgetWin_1"` e trazê-la para o primeiro plano com `SetForegroundWindow`.
3. **Simular Clique Central e Mouse Wheel:** Posicionar o cursor no meio do container dos termos e disparar múltiplos eventos `MOUSEEVENTF_WHEEL` (delta negativo, e.g. -240).
4. **Acionar o Botão "Aceitar" via UI Automation (UIA):** Varrer a árvore UIA da janela até encontrar o botão com nome `"Aceitar"` com `IsEnabled: True` e invocar seu `InvokePattern.Invoke()` ou clicar nas suas coordenadas.
5. **Feedback Sonoro:** Emitir bipes com `[Console]::Beep` para orientar usuários cegos ou de baixa visão sobre o progresso e a conclusão da ação.

---

## Script Completo de Automação (PowerShell / C#)

O código abaixo pode ser salvo como `aceitar_termos_lol.ps1` e executado em qualquer máquina Windows:

```powershell
Write-Host "Iniciando assistente de acessibilidade..." -ForegroundColor Cyan

# Bipe de aviso sonoro
try { [Console]::Beep(800, 200) } catch {}

Add-Type -ReferencedAssemblies "UIAutomationClient", "UIAutomationTypes", "WindowsBase" -TypeDefinition @"
using System;
using System.Threading;
using System.Runtime.InteropServices;
using System.Windows.Automation;
using System.Text;

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

            // 1. Encontrar janela do Riot Client
            IntPtr riotHwnd = IntPtr.Zero;
            RECT riotRect = new RECT();

            EnumWindows((hWnd, lParam) => {
                if (IsWindowVisible(hWnd)) {
                    StringBuilder title = new StringBuilder(256);
                    StringBuilder cls = new StringBuilder(256);
                    GetWindowText(hWnd, title, 256);
                    GetClassName(hWnd, cls, 256);

                    if (title.ToString().Contains("Riot Client") || (cls.ToString() == "Chrome_WidgetWin_1" && title.ToString() != "")) {
                        RECT r;
                        GetWindowRect(hWnd, out r);
                        int w = r.Right - r.Left;
                        int h = r.Bottom - r.Top;
                        if (w > 400 && h > 300) {
                            riotHwnd = hWnd;
                            riotRect = r;
                            return false;
                        }
                    }
                }
                return true;
            }, IntPtr.Zero);

            if (riotHwnd == IntPtr.Zero) {
                status = "AVISO: Janela do Riot Client nao encontrada.";
                CloseDesktop(hDesk);
                return;
            }

            // 2. Focar janela
            SetForegroundWindow(riotHwnd);
            Thread.Sleep(500);

            // 3. Posicionar no centro e clicar
            int centerX = riotRect.Left + (riotRect.Right - riotRect.Left) / 2;
            int centerY = riotRect.Top + (riotRect.Bottom - riotRect.Top) / 2;
            SetCursorPos(centerX, centerY);
            Thread.Sleep(100);

            mouse_event(0x0002, 0, 0, 0, 0); // DOWN
            mouse_event(0x0004, 0, 0, 0, 0); // UP
            Thread.Sleep(100);

            // 4. Rolar para baixo (mouse wheel)
            for (int i = 0; i < 150; i++) {
                mouse_event(0x0800, 0, 0, -240, 0);
                Thread.Sleep(10);
            }

            Thread.Sleep(1000);

            // 5. Clicar em Aceitar via UI Automation
            bool clicado = false;
            try {
                AutomationElement root = AutomationElement.FromHandle(riotHwnd);
                if (root != null) {
                    var cond = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button);
                    var btns = root.FindAll(TreeScope.Descendants, cond);
                    foreach (AutomationElement b in btns) {
                        if (b.Current.Name.Contains("Aceitar") && b.Current.IsEnabled) {
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

            status = clicado ? "SUCESSO: Termos aceitos!" : "ROLADO: Rolagem concluida com sucesso.";
            CloseDesktop(hDesk);
        }));

        t.Start();
        t.Join();
        return status;
    }
}
"@

$res = [RiotAccessibilityHelper]::ExecuteWorkflow()
Write-Host $res -ForegroundColor Green
if ($res -like "*SUCESSO*") {
    try {
        [Console]::Beep(1200, 150)
        Start-Sleep -Milliseconds 100
        [Console]::Beep(1600, 300)
    } catch {}
}
```

---

## Instruções para o Arquivo `.bat` (Execução com 1 Clique)

Para que qualquer pessoa possa executar sem precisar abrir o terminal ou digitar comandos:

Crie o arquivo `aceitar_termos_lol.bat`:
```bat
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\aceitar_termos_lol.ps1"
pause
```

---

## Como Usar com um Agente de IA

Se uma IA estiver ajudando um usuário com o mesmo problema:
1. A IA deve executar o script diretamente no terminal PowerShell ou chamar `LoLToSHelper.scroll_and_accept_sync()`.
2. Como o script gerencia a conexão com a desktop `Default`, a IA não precisa pedir para o usuário alternar janelas manualmente.
3. Após a execução, a IA pode verificar se o diálogo sumiu ou se o botão foi clicado inspecionando os elementos via UI Automation.

---

## Erros Comuns e Cuidados
- **Não tentar usar `SetCursorPos` sem nova thread / `SetThreadDesktop`**: Em subprocessos do Windows disparados por daemons de IA, `SetCursorPos` retorna `False` sem erro explícito. A alocação em thread separada com `OpenDesktop("Default", 0, false, 0x01FF)` é mandatória.
- **Não depender de teclas como `PageDown`**: O container web da Riot simplesmente descarta teclas de rolagem quando não há foco editável. A rolagem DEVE ser simulada via `MOUSEEVENTF_WHEEL`.
- **Bipes sonoros são essenciais**: Para usuários com deficiência visual usando leitor de telas, bipes em frequências distintas fornecem confirmação imediata de início e término.
