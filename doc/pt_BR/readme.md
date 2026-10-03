# lolAccessibility - Acessibilidade para League of Legends e Riot Client (NVDA)

O **lolAccessibility** é um add-on completo para o leitor de telas **NVDA** que integra as três camadas de API da Riot Games para criar uma experiência de jogo 100% acessível para pessoas cegas e com baixa visão:
1. **Riot Client UI & Launcher**: Elimina anúncios de "animation" e rotula controles do inicializador.
2. **League Client (LCU API)**: Suporte completo ao pré-jogo (Lobby, Fila, Ready Check e Seleção de Campeões).
3. **Live Client Data API (127.0.0.1:2999)**: Motor de áudio e fala em tempo real durante a partida ao vivo (Vida, Recursos, KDA, Itens, Habilidades, Eventos de Abate, Dragões, Torres e Avisos de Perigo).

---

## 🎯 Principais Recursos

### 1. Inicializador (Riot Client)
- **Silenciamento de nós decorativos**: Mascara elementos em SVG e animações Lottie que eram lidos repetidamente como "animation".
- **Fim dos alertas do Chromium**: Neutraliza os avisos de *"Para ver descrições ausentes de imagens..."*.
- **Rotulação Acessível**: Identifica botões de Perfil, Amigos, Configurações, Notificações, Minimizar e Fechar.
- **Progresso de Download**: Atalho dedicado para ler velocidade, tamanho baixado e tempo restante.
- **Automação de Termos de Serviço (ToS) (`Control + Shift + T` ou `NVDA + Shift + T`)**: Rola automaticamente o container web CEF/Chromium e clica em Aceitar, contornando a barreira onde o botão permanece desabilitado ("Role para aceitar") e o teclado é ignorado. Também disponível via arquivo de 1 clique `aceitar_termos_lol.bat`.

### 2. Saguão e Seleção de Campeões (League Client)
- **Assistente de Seleção e Travamento de Campeões (`Control + Shift + P`)**:
  - Digite o nome do campeão (ex: `Garen`, `Ashe`, `Lee`, `TF`) em um diálogo acessível.
  - O add-on localiza o campeão, realiza o travamento imediato (`lock-in`) e importa automaticamente a melhor página de runas da Riot com os feitiços de invocador ideais.
- **Suporte Total ao Modo ARAM (`Control + Shift + B` e `Control + Shift + D`)**:
  - Fala imediatamente o campeão sorteado ao entrar na seleção.
  - Abre o banco de reservas de campeões para troca rápida com apenas um clique (`Control + Shift + B`).
  - Rola o dado do ARAM para sortear outro campeão (`Control + Shift + D`).
- **Importador de Runas e Feitiços com 1 Toque (`Control + Shift + R`)**:
  - Aplica instantaneamente as runas e feitiços oficiais de alta taxa de vitória para o seu campeão e rota.
- **Seletor de Rotas no Saguão (`Control + Shift + O`)**:
  - Escolha suas preferências de rota (Topo, Selva, Meio, Atirador, Suporte ou Preencher) com diálogo acessível.
- **Alerta Sonoro e F6 para Aceitar Partida**: Toca bips sonoros e permite aceitar o Ready Check com apenas uma tecla.
- **Modo Auto-Aceitar**: Opcionalmente aceita a partida encontrada de forma automática (`Control + Shift + F6`).
- **Contagem Regressiva e Alertas Sonoros**: Avisos aos 30s, 15s e bips regressivos a cada segundo nos últimos 5 segundos da seleção.
- **Leitor de Chat**: Anuncia mensagens recentes enviadas no chat do saguão/time.

### 3. Durante a Partida ao Vivo (Live Client Data API 127.0.0.1:2999)
- **Dedução Inteligente de Rotas dos Inimigos (Etapa 1)**:
  - Analisa automaticamente feitiços de invocador (Smite/Golpear para Selva), itens iniciais (Atlas Mundial para Suporte, brotinhos de selva) e arquétipos dos campeões para informar quem está em cada rota (Topo, Selva, Meio, Atirador e Suporte), ou Rota Única no ARAM.
  - Alerta automático falado ao completar 1 minuto de partida (quando os minions começam a marchar).
  - Atalho `Control + Shift + E` sob demanda (1 toque: rotas; 2 toques rápidos: feitiços de invocador de cada inimigo).
- **Leitor de Pings Táticos e Chat dos Aliados (Etapa 2)**:
  - **Captura Ultrarrápida e Não-Invasiva (< 4ms)**: Monitora a caixa de chat do jogo via GDI Windows API e motor OCR integrado, com total conformidade com o anti-cheat **Riot Vanguard** (zero injeção / zero hooks de memória).
  - **Reconhecimento Inteligente de Pings**:
    - **Inimigo Desaparecido (MIA / `?`)**: Emite som oco descendente de alerta e fala *"Alerta de MIA: [Campeão] desapareceu da rota!"*.
    - **Perigo (`!`)**: Emite som agudo de perigo e fala *"Alerta de Perigo sinalizado por [Campeão]!"*.
    - **A Caminho**: Emite acorde musical ascendente alegre e fala *"[Campeão] a caminho!"*.
    - **Cuidado / Recuar**: Emite aviso sonoro e fala *"Cuidado! Sinal de recuo por [Campeão]!"*.
    - **Ajuda / Assistência**: Emite pulsos sonoros e fala *"[Campeão] pede ajuda!"*.
    - **Feitiços de Invocador**: Anuncia feitiços sinalizados (ex: *"Flash (250s)"* ou *"Flash pronto"*).
    - **Mensagens de Chat**: Lê mensagens enviadas no chat do time ou geral.
  - **Filtro Anti-Spam Inteligente**: Se um aliado der vários pings repetidos em poucos segundos, o add-on agrupa os avisos e evita poluição sonora.
  - **Atalhos Dedicados**:
    - `Control + Shift + M` ou `M`: 1 toque lê os últimos 3 pings/mensagens; 2 toques rápidos força uma varredura completa da tela naquele instante.
    - `Control + Shift + F7`: Ativa ou desativa a leitura automática de pings durante a partida.
- **Motor de Eventos Táticos Detalhados**:
  - Anuncia Primeiro Abate (*First Blood*), Arauto do Vale (*Herald*), Barão Na'Shor, Dragões elementais, torres destruídas com rota identificada (Topo, Meio, Inferior e time) e Ás!
- **Alerta Sonoro de Vida Crítica (Low HP Beeps)**: Emite pulsos sonoros rápidos quando a vida do seu campeão cair abaixo de 25%.
- **Alerta de Subida de Nível (Level Up)**: Sinal sonoro agradável e aviso por voz indicando que você subiu de nível.
- **Consultas Rápidas por Atalhos**:
  - Vida e Mana com porcentagens exatas e ouro acumulado.
  - Placar KDA e quantidade de tropas eliminadas (CS).
  - Itens e feitiços de invocador no inventário.
  - Níveis de cada habilidade (Q, W, E, R).
  - Inimigos vivos e mortos com tempo de renascimento.
  - Tempo de jogo decorrido.

---

## ⌨️ Tabela Completa de Atalhos de Teclado

### No Riot Client (Janela do inicializador)
| Atalho | Ação |
| :--- | :--- |
| `Control + Shift + T` ou `NVDA + Shift + T` | **Rolar e Aceitar Termos de Serviço (ToS)** automaticamente. |
| `Control + Shift + D` ou `NVDA + Shift + D` | Anunciar velocidade e progresso do download/instalação. |
| `Control + Shift + S` ou `NVDA + Shift + S` | Anunciar usuário autenticado (Riot ID#tag) e status Online. |
| `Control + Shift + J` ou `NVDA + Shift + J` | Mover o foco para o botão principal de ação (Jogar/Instalar) ou aceitar termos. |
| `NVDA + Shift + H` | Ajuda rápida dos atalhos do add-on. |

### No League Client (Pré-jogo / Saguão / Seleção de Campeões)
| Atalho | Ação |
| :--- | :--- |
| `F6` ou `NVDA + F6` | **Aceitar partida encontrada (Ready Check)** instantaneamente. |
| `Control + Shift + F6` | Ativar / Desativar a **Aceitação Automática** de partidas. |
| `Control + Shift + T` ou `NVDA + Shift + T` | **Rolar e Aceitar Termos de Serviço (ToS)** automaticamente. |
| `Control + Shift + P` ou `NVDA + Shift + P` | **Escolher e Travar Campeão** (com runas e feitiços automáticos). |
| `Control + Shift + B` ou `NVDA + Shift + B` | **Banco do ARAM** (trocar campeão) ou **Banir Campeão**. |
| `Control + Shift + D` ou `NVDA + Shift + D` | **Rolar Dado no ARAM** (ou ver download no Launcher). |
| `Control + Shift + R` ou `NVDA + Shift + R` | **Importar Runas e Feitiços** recomendados oficiais da Riot. |
| `Control + Shift + O` ou `NVDA + Shift + O` | **Escolher Rotas no Saguão** (Top, Jungle, Mid, Bot, Sup). |
| `Control + Shift + C` ou `NVDA + Shift + C` | **Detalhes da Seleção de Campeões** (fase, time, campeão e timer). |
| `Control + Shift + J` ou `NVDA + Shift + J` | Iniciar busca de partida, aceitar termos ou interagir com tutoriais. |
| `Control + Shift + S` ou `NVDA + Shift + S` | Perfil do invocador (nível, XP e ranqueada). |
| `Control + Shift + Escape` | Fechar e confirmar diálogos/termos modais pendentes. |

### Durante a Partida ao Vivo (In-Game - 127.0.0.1:2999)
| Atalho | Ação |
| :--- | :--- |
| `NVDA + Shift + W` ou `Alt + F10` | **Focar e Restaurar Jogo**: Traz a janela da partida para o primeiro plano em tela cheia (sem colidir com atalhos de navegadores). |
| `Alt + 1` | **Mover para Topo**: Anda automaticamente pelo pathfinding do minimapa para a Rota Superior. |
| `Alt + 2` | **Mover para o Meio**: Anda automaticamente pelo pathfinding do minimapa para a Rota do Meio. |
| `Alt + 3` | **Mover para Rota Inferior**: Anda automaticamente pelo pathfinding do minimapa para a Rota Inferior. |
| `Alt + 4` | **Mover para Base Aliada**: Anda automaticamente pelo minimapa de volta à Fonte segura. |
| `Alt + Espaço` | **Centralizar Câmera e Cursor**: Trava a câmera no campeão e centraliza o mouse. |
| `Control + Shift + N` ou `NVDA + Shift + N` | **Menu de Navegação no Minimapa**: Abre lista com todos os destinos (rotas, torres e dragão/barão). |
| `Control + Shift + M` ou `M` | **Radar de Áudio Espacial 3D**: Varredura acústica com bips estéreo direcionais e anúncio falado. |
| `Control + Shift + R` | Alternar **Radar de Proximidade Espacial Automático** (Ligado / Desligado). |
| `P` ou `Control + Shift + P` | **Loja Acessível de Itens**: Mostra ouro, itens para fechar agora, valores restantes e compra com Enter. |
| `B` | **Guia Sonoro de Retorno à Base (Recall)**: Acompanha os 8s com som progressivo e alerta se sofrer dano. |
| `U` ou `Control + Shift + U` | **Habilidades**: Anuncia tempos de recarga exatos em segundos e níveis de Q, W, E e R. |
| `Control + Shift + K` | **Placar Geral / KDA**: KDA pessoal, tropas eliminadas (CS) e placar geral de abates da partida. |
| `Control + Shift + S` | **Estatísticas do Campeão**: Vida e Mana (atuais/máx em %), Nível, Dano, Armadura, Velocidade e Alcance. |
| `Control + Shift + O` | **Objetivos e Tempo**: Tempo de jogo decorrido, Dragões, Barões e Torres destruídas de cada time. |
| `Control + Shift + E` | **Inimigos e Feitiços**: Rotas deduzidas dos inimigos, feitiços de invocador e tempo de renascimento. |
| `Control + Shift + F8` | Alternar **Alerta Automático de Emboscada / Gank** (Ligado / Desligado). |
| `Control + Shift + F7` | Alternar **Leitura Automática de Pings e Chat** (Ligada / Desligada). |

### Atalhos Globais (Funcionam de Qualquer Janela no Windows sem Conflitos)
| Atalho | Ação |
| :--- | :--- |
| `NVDA + F6` | **Aceitar Partida Encontrada (Ready Check)** de qualquer janela. |
| `Control + Shift + F6` | Alternar **Aceitação Automática** de partidas. |
| `NVDA + Shift + L` | **Status Geral**: Situação do Riot Client, League Client, saguão e partida ao vivo. |
| `NVDA + Shift + S` | **Perfil do Usuário**: Riot ID, nível do invocador e elo ranqueado. |
| `NVDA + Shift + D` | **Download / Instalação**: Progresso e velocidade de download do LoL. |
| `NVDA + Shift + J` | **Botão Principal**: Pressionar Jogar, Instalar ou confirmar avisos modais. |
| `NVDA + Shift + P` | **Assistente de Campeões**: Escolher e travar campeão na Seleção de Campeões. |
| `NVDA + Shift + B` | **ARAM / Banimento**: Gerenciar banco do ARAM ou banir campeão. |
| `NVDA + Shift + R` | **Runas Oficiais**: Importar melhores runas e feitiços recomendados. |
| `NVDA + Shift + O` | **Rotas no Saguão**: Configurar preferências de rotas (*Top, Jg, Mid, Bot, Sup*). |
| `NVDA + Shift + C` | **Seleção de Campeões**: Detalhes da fase, campeões e tempo restante. |
| `NVDA + Shift + W` | **Focar Jogo**: Restaurar e focar a janela da partida 3D do League of Legends. |
| `NVDA + Shift + H` | **Ajuda**: Lista falada de todos os atalhos disponíveis. |


---

## 🛡️ Segurança e Conformidade com o Riot Vanguard

O **lolAccessibility** foi projetado respeitando integralmente as diretrizes da Riot Games:
- **Zero injeção de memória**: Não toca na memória de processos do jogo.
- **APIs Oficiais e Aprovadas**:
  - A **Live Client Data API (127.0.0.1:2999)** é oficialmente documentada e mantida pela Riot Games especificamente para ferramentas de terceiros durante a partida.
  - A **League Client API (LCU)** é acessada via lockfile local, do mesmo modo que aplicações como Blitz, Porofessor e Mobalytics.
- **100% seguro**: Total conformidade com o anti-cheat **Riot Vanguard**.
