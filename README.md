# lolAccessibility 🎮♿

**Add-on de Acessibilidade Total para League of Legends e Riot Client no Leitor de Telas NVDA**

[![Release](https://img.shields.io/github/v/release/jhonata192/lolAccessibility?color=brightgreen&label=Vers%C3%A3o)](https://github.com/jhonata192/lolAccessibility/releases)
[![NVDA](https://img.shields.io/badge/NVDA-2023.1%20%7C%202024.1%2B-blue)](https://www.nvaccess.org/)
[![License](https://img.shields.io/badge/Licen%C3%A7a-GPLv2%2B-orange)](LICENSE)
[![Riot Vanguard](https://img.shields.io/badge/Riot%20Vanguard-100%25%20Compat%C3%ADvel%20%26%20Seguro-success)](#-segurança-e-conformidade-com-o-riot-vanguard)

---

## 📥 Download

Você pode baixar a versão compilada mais recente diretamente na página de lançamentos:

👉 **[Baixar lolAccessibility.nvda-addon (Última Versão)](https://github.com/jhonata192/lolAccessibility/releases/latest)**

Para instalar, basta abrir o arquivo baixado com o **NVDA** em execução e confirmar a instalação, ou instalá-lo através do menu do NVDA (*Ferramentas -> Gerenciar Complementos -> Instalar*).

---

## 🌟 Visão Geral

O **lolAccessibility** foi desenvolvido para transformar o **League of Legends** e o **Riot Client** em uma experiência totalmente acessível para pessoas cegas e com baixa visão.

Ele integra as três camadas oficiais de interface e dados disponibilizados pela Riot Games:
1. **Riot Client UI & Launcher**: Acessibilidade no inicializador, limpeza de ruídos Chromium/SVG e acompanhamento do progresso de downloads.
2. **League Client (LCU API)**: Suporte completo ao pré-jogo (Saguão, Fila, Ready Check, Diálogo acessível com busca e travamento de Campeões, Importação automática de Runas e Feitiços e Modo ARAM).
3. **Live Client Data API (127.0.0.1:2999)**: Motor tático de fala, áudio espacial e navegação durante a partida ao vivo em 3D.

---

## 🚀 Principais Funcionalidades

### 1. Navegação Tática no Minimapa por Pathfinding
- **Autonomia Total de Movimentação**: Elimina a necessidade de adivinhar coordenadas no espaço 3D.
- Utiliza o motor nativo de *pathfinding* do jogo com cliques programáticos no minimapa. Seu campeão desvia de obstáculos, contorna paredes e caminha com segurança.
- **Movimentação Direta por Atalhos**:
  - `Alt + 1`: Caminhar para a **Rota Superior (Top Lane)**.
  - `Alt + 2`: Caminhar para a **Rota do Meio (Mid Lane)**.
  - `Alt + 3`: Caminhar para a **Rota Inferior (Bot Lane)**.
  - `Alt + 4`: Retornar para a **Base Aliada (Fonte)**.
  - `Alt + Espaço`: Centralizar a câmera no campeão e alinhar o mouse.
- **Menu Completo de Navegação (`Control + Shift + N`)**: Permite selecionar waypoints do mapa (rotas, torres aliadas e covis de Dragão/Barão).

### 2. Painel Tático In-Game Sob Demanda
- **Placar e KDA (`Control + Shift + K`)**: Abates, mortes, assistências, tropas eliminadas (*CS*), placar geral e diferença de abates.
- **Estatísticas Completas (`Control + Shift + S`)**: Nível, Vida e Recursos (atual/máximo e %), AD, AP, Armadura, Resistência Mágica, Velocidade de Movimento e Alcance de Ataque.
- **Objetivos Globais (`Control + Shift + O`)**: Tempo decorrido de partida, contagem de Dragões, Barões e Torres destruídas de cada equipe.
- **Inimigos e Feitiços (`Control + Shift + E`)**: Status dos adversários (vivos ou tempo restante de renascimento), rotas deduzidas e feitiços de invocador (*Flash, Incendiar, etc.*).

### 3. Assistente de Loja e Receitas de Itens (`P` ou `Control + Shift + P`)
- Analisa seu inventário e ouro disponível em tempo real.
- Informa itens completos prontos para fechamento imediato e calcula exatamente quanto ouro falta para os itens em construção.
- Permite comprar itens pelo teclado pressionando `Enter` na lista acessível.

### 4. Monitor de Combate, Vida Crítica e Recall Guard
- **Pulsos Cardíacos de Perigo**: Emite som de batimentos cardíacos (*heartbeat*) quando sua vida fica abaixo de 30%.
- **Recall Guard (`B`)**: Acompanha a canalização do retorno à base com guia acústico progressivo de 8 segundos e alerta imediatamente se você sofrer dano ou tiver a canalização interrompida.
- **Status de Habilidades (`U`)**: Anuncia os tempos de recarga exatos e níveis de Q, W, E e R, com aviso especial quando a Ultimate estiver pronta.

### 5. Radar de Áudio Espacial 3D (`M` e `Control + Shift + R`)
- Áudio PCM estéreo binaural nativo do Windows com lei de potência constante de panning.
- Mapeia distância para frequência de bips sonoros e informa posições de adversários em horas de relógio (ex: *"Inimigo às 3 horas, próximo"*).

### 6. Leitor de Pings Táticos e Chat dos Aliados
- Leitura não-invasiva e de altíssima velocidade (< 4ms) via GDI Windows API e OCR.
- Reconhece e sonoriza com efeitos dedicados: **Inimigo Desaparecido (MIA / `?`)**, **Perigo (`!`)**, **A Caminho**, **Ajuda**, **Cuidado** e feitiços pingados.
- **Filtro Anti-Spam Inteligente**: Evita sobrecarga sonora quando um aliado sinaliza múltiplos pings em sequência.

### 7. Saguão, Fila e Seleção de Campeões
- **Ação Principal Inteligente (`Control + Shift + J`)**: Inicia ou cancela busca de partida, aceita termos e interage com diálogos de tutorial.
- **Aceitar Partida Instantaneamente (`F6`)**: Com opção de auto-aceitação (`Control + Shift + F6`).
- **Seletor Acessível de Campeões (`Control + Shift + P`)**: Lista com busca rápida e navegação por setas para escolher e travar campeões habilitados, com importação automática de runas e feitiços oficiais recomendados.
- **Suporte ao Modo ARAM (`Control + Shift + B` e `Control + Shift + D`)**: Troca no banco de reservas e rolagem de dados.
- **Rotas no Saguão (`Control + Shift + O`)**: Configuração facilitada de preferências de rotas (*Top, Jungle, Mid, Bot, Sup*).

### 8. Isolamento Estrito de Foco (Zero Key Hijacking)
- **Sem Interceptação em Outros Aplicativos**: Os atalhos in-game só são processados quando a janela 3D da partida (`RiotWindowClass`) estiver em primeiro plano.
- Teclas padrão do Windows e navegadores como `Control + Shift + T` (reabrir abas), `Control + Shift + N` (janela anônima), `Control + Shift + P` (paleta do VS Code) e `Alt + Espaço` continuam funcionando 100% normalmente em todos os outros programas.

---

## ⌨️ Tabela de Atalhos

### Durante a Partida ao Vivo (In-Game - 127.0.0.1:2999)
| Atalho | Ação |
| :--- | :--- |
| `NVDA + Shift + W` ou `Alt + F10` | **Focar e Restaurar Jogo**: Traz a janela da partida para o primeiro plano em tela cheia. |
| `Alt + 1` | **Mover para Topo**: Caminha automaticamente pelo minimapa para a Rota Superior. |
| `Alt + 2` | **Mover para o Meio**: Caminha automaticamente pelo minimapa para a Rota do Meio. |
| `Alt + 3` | **Mover para Rota Inferior**: Caminha automaticamente pelo minimapa para a Rota Inferior. |
| `Alt + 4` | **Mover para Base Aliada**: Caminha automaticamente de volta à Fonte segura. |
| `Alt + Espaço` | **Centralizar Câmera e Cursor**: Trava a câmera no campeão e centraliza o mouse. |
| `Control + Shift + N` ou `NVDA + Shift + N` | **Menu de Navegação no Minimapa**: Abre lista com todos os destinos táticos. |
| `Control + Shift + M` ou `M` | **Radar de Áudio Espacial 3D**: Varredura acústica com bips estéreo e anúncio falado. |
| `Control + Shift + R` | Alternar **Radar de Proximidade Espacial Automático**. |
| `P` ou `Control + Shift + P` | **Loja Acessível de Itens**: Consulta de ouro, fechamento de itens e compra com Enter. |
| `B` | **Guia Sonoro de Retorno à Base (Recall)**: Monitor sonoro com alerta de dano. |
| `U` ou `Control + Shift + U` | **Habilidades**: Níveis e tempos de recarga de Q, W, E e R. |
| `H` ou `Control + Shift + H` | **Vida e Recursos**: Vida, Mana/Energia e Ouro. |
| `Control + Shift + K` | **Placar Geral / KDA**: Abates, mortes, assistências, tropas (CS) e placar total. |
| `Control + Shift + S` | **Estatísticas Detalhadas**: Vida, Mana, Nível, AD, AP, Armadura, MR, Velocidade e Alcance. |
| `Control + Shift + O` | **Objetivos e Tempo**: Tempo de jogo decorrido, Dragões, Barões e Torres. |
| `Control + Shift + E` | **Inimigos e Feitiços**: Rotas deduzidas dos adversários, feitiços e tempo de renascimento. |
| `Control + Shift + F8` | Alternar **Alerta Automático de Emboscada / Gank**. |
| `Control + Shift + F7` | Alternar **Leitura Automática de Pings e Chat**. |

### No Inicializador e League Client (Pré-Jogo)
| Atalho | Ação |
| :--- | :--- |
| `F6` ou `NVDA + F6` | **Aceitar Partida Encontrada (Ready Check)** instantaneamente. |
| `Control + Shift + F6` | Alternar **Aceitação Automática** de partidas. |
| `Control + Shift + P` ou `NVDA + Shift + P` | **Escolher e Travar Campeão** (com runas e feitiços automáticos). |
| `Control + Shift + B` ou `NVDA + Shift + B` | **Banco do ARAM** (trocar campeão) ou **Banir Campeão**. |
| `Control + Shift + D` ou `NVDA + Shift + D` | **Rolar Dado no ARAM** ou Progresso de Download no Launcher. |
| `Control + Shift + R` ou `NVDA + Shift + R` | **Importar Runas e Feitiços Recomendados**. |
| `Control + Shift + O` ou `NVDA + Shift + O` | **Escolher Rotas no Saguão** (Top, Jungle, Mid, Bot, Sup). |
| `Control + Shift + C` ou `NVDA + Shift + C` | **Detalhes da Seleção de Campeões** (fase, time, campeão e tempo restante). |
| `Control + Shift + J` ou `NVDA + Shift + J` | Iniciar busca de partida ou clicar em botões principais de ação. |
| `NVDA + Shift + L` ou `Control + Shift + L` | Status geral dos serviços Riot, League Client e partida ao vivo. |
| `NVDA + Shift + H` | Ajuda rápida de atalhos. |

---

## 🛡️ Segurança e Conformidade com o Riot Vanguard

O **lolAccessibility** foi desenvolvido em total conformidade com as políticas da Riot Games e o sistema anti-cheat **Riot Vanguard**:
- **Zero injeção de DLLs e Zero hooks de memória**: O add-on não injeta bibliotecas nem modifica o executável do jogo.
- **APIs Oficiais e Documentadas**:
  - A **Live Client Data API (127.0.0.1:2999)** é uma interface HTTP local fornecida oficialmente pela Riot Games especificamente para ferramentas de terceiros durante a partida.
  - A **League Client API (LCU)** é consultada através do lockfile de autenticação local gerado pelo próprio inicializador.
- **Captura Passiva de Tela**: A leitura de pings e chat utiliza chamadas nativas de GDI do Windows (`BitBlt`), da mesma forma que ferramentas de gravação (OBS, Discord) e capturas de tela.

---

## 🛠️ Desenvolvimento e Testes

Para executar a suíte completa de testes automatizados do projeto:

```powershell
python tests/test_addon.py
```

Para gerar o pacote instalável `.nvda-addon`:

```powershell
python build.py
```

Para instalar e recarregar automaticamente no seu NVDA local:

```powershell
python install_addon.py
```

---

## 📄 Licença

Distribuído sob a licença **GNU General Public License v2.0** (ou posterior), em conformidade com o ecossistema de add-ons do NVDA.
