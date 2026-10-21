# Live Pulse

Projeto universitário para os **Níveis 1 e 2 do desafio técnico da jeKnowledge**.
Aplicação de votações com uma área para o público e um painel do anfitrião.
Interface em português de Portugal. Não inclui o Nível 3.

## Executar no Windows

Requisitos: Python 3.13 e Node.js 22.12 ou superior, com npm.
O projeto foi verificado com Python 3.13.5 e Node.js 24.18.0.
Abra dois terminais PowerShell na pasta `desafio_jek`.

**Terminal 1 — backend:**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Se `backend/venv` já existir, omita a criação do ambiente virtual.
Os comandos usam diretamente o Python do ambiente; não é necessário alterar a política
de execução do PowerShell nem ativar o ambiente.

**Terminal 2 — frontend:**

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Abra:

- Público: <http://127.0.0.1:5173/#publico>
- Anfitrião: <http://127.0.0.1:5173/#anfitriao>

Mantenha os dois terminais abertos. Use `Ctrl+C` para parar cada servidor.
A aplicação começa sem votações de demonstração. Crie uma no painel do anfitrião.
O frontend usa `http://127.0.0.1:8000/api` por omissão.
Se necessário, defina `VITE_API_URL` num ficheiro `frontend/.env` e reinicie o Vite.
As origens locais na porta 5173 estão autorizadas na configuração CORS do Django.

## Experimentar o fluxo completo

1. No painel do anfitrião, introduza uma pergunta e entre 2 e 5 opções.
2. Guarde o rascunho. O público ainda não o consegue ver.
3. Prima **Abrir votação**. Na área pública, prima **Atualizar lista**.
4. Selecione uma opção e prima **Registar voto**. Surge a confirmação.
5. No anfitrião, prima **Atualizar resultados** para ver a contagem e as barras.
6. Um segundo voto do mesmo navegador na mesma votação é recusado pelo backend.
7. Feche a votação no painel. Atualize a lista pública para consultar os resultados.

## Funcionalidades

### Nível 1

- Criação de votações com uma pergunta e 2 a 5 opções.
- Estado inicial Rascunho; transições Rascunho → Aberta → Fechada.
- O público só recebe votações Abertas e Fechadas.
- Votação em opções de votações Abertas, com mensagem de confirmação.
- Resultados disponíveis em qualquer estado para o anfitrião.
- Resultados públicos disponíveis apenas depois do fecho.
- Botões para atualizar manualmente as listas e os resultados.

### Nível 2

- Um UUID é gerado com `crypto.randomUUID()` e guardado no `localStorage`.
- O backend valida o UUID e impede um segundo voto com o mesmo token na mesma votação.
- A base de dados também impõe a unicidade do par `(poll, token)`.
- O backend recusa votos em rascunhos ou votações fechadas e opções de outra votação.
- Validação de pergunta/opções vazias, tipos inválidos, limites de 255 caracteres,
  opções repetidas (ignorando maiúsculas e espaços exteriores) e quantidade de opções.
- Mensagens de erro visíveis e estados de carregamento.
- Contagens, percentagens e gráficos de barras em CSS, incluindo resultados sem votos.
- Layout responsivo, formulários com etiquetas e navegação por teclado.

## Tecnologias e organização

- **Python e Django:** aproveitam o backend existente; o ORM permite trabalhar com
  os modelos e migrações sem escrever SQL manualmente.
- **Django REST Framework:** valida os pedidos e transforma os modelos em JSON.
- **SQLite:** uma base de dados num ficheiro, suficiente para este projeto local.
- **React e Vite, com JavaScript:** componentes e estado para os formulários, listas
  e resultados, com um servidor de desenvolvimento simples e um build estático.
- **CSS simples e fetch:** sem bibliotecas de componentes, gráficos ou cliente HTTP.

```text
backend/
  config/settings.py       Configuração de Django, SQLite e CORS
  config/urls.py           Entrada da API
  polls/models.py         Poll, Option e Vote
  polls/serializers.py    Validação dos pedidos e conversão para JSON
  polls/views.py          Regras dos endpoints
  polls/urls.py           Rotas do público e do anfitrião
  polls/migrations/       Evolução da base de dados
  polls/tests.py          Testes automáticos do backend
frontend/
  src/api.js             Pedidos fetch e token do navegador
  src/main.jsx           Componentes React e navegação entre áreas
  src/style.css          Estilos e adaptação a ecrãs pequenos
  tests/                 Testes da interface com Playwright
```

Os três modelos originais foram conservados. `Vote` passou a guardar também `poll`
e `token`. A migração `0002` associa eventuais votos antigos à votação da sua opção
e atribui um UUID diferente a cada um antes de aplicar a restrição de unicidade.
A base de dados existente não é apagada pelas migrações.

## API REST

Todos os caminhos seguintes têm o prefixo `http://127.0.0.1:8000/api/`.

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `public/polls/` | Listar votações Abertas e Fechadas, sem contagens |
| POST | `public/polls/<id>/vote/` | Registar um voto |
| GET | `public/polls/<id>/results/` | Resultados de uma votação Fechada |
| GET | `host/polls/` | Listar todas as votações |
| POST | `host/polls/` | Criar um Rascunho |
| PATCH | `host/polls/<id>/status/` | Abrir ou fechar uma votação |
| GET | `host/polls/<id>/results/` | Resultados em qualquer estado |

Exemplos de corpos JSON:

```json
{"question": "Que linguagem preferes?", "options": ["C", "Python", "Java"]}
```

```json
{"status": "open"}
```

```json
{"option_id": 1, "token": "6399b8ae-e189-4b8c-8de1-deb5d429d9b0"}
```

Respostas: `201` para criação/voto, `200` para consultas/transições,
`400` para dados ou transições inválidos, `403` para resultados públicos ainda
indisponíveis, `404` para votações inexistentes ou rascunhos na API pública e
`409` para votos duplicados ou uma transição cujo estado mudou entretanto.

## Verificação automática

Na pasta `backend`:

```powershell
.\venv\Scripts\python.exe manage.py test --verbosity 2
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Os 18 testes cobrem criação/validação, visibilidade, transições, voto, UUID,
duplicação, unicidade na base de dados, resultados, percentagens e conservação
de votos antigos na migração. Usam uma base de dados de testes separada.

Na pasta `frontend`:

```powershell
npm.cmd run build
```

Para testar a interface num Chromium sem janela (instalação do navegador apenas
na primeira execução):

```powershell
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Estes testes abrem os dois servidores automaticamente e usam uma base SQLite
temporária na porta 8001. Não alteram a base de dados da aplicação.
As portas 5173 e 8001 devem estar livres; pare o Vite normal antes de executar.
Verificam o fluxo completo de criar/abrir/votar/fechar, o token após recarregar,
a rejeição de voto duplicado, a publicação dos resultados e o formulário num
ecrã de 375 px. A configuração destes testes está preparada para Windows.
`npm.cmd run format` formata os ficheiros do frontend com Prettier.

O build fica em `frontend/dist`. `npm.cmd run preview` permite inspecioná-lo;
o backend continua a ser necessário. O comando normal para demonstração é
`npm.cmd run dev`, na porta 5173 autorizada pelo CORS.

Verificação realizada: migrações aplicadas, 18 testes Django e 2 testes de
navegador aprovados, `manage.py check` sem problemas, nenhuma migração em falta
e `npm.cmd run build` concluído com sucesso.

## Limitações e decisões

- **Não existe autenticação**, conforme pedido. A separação entre público e
  anfitrião organiza as interfaces e os endpoints, mas não identifica pessoas:
  qualquer utilizador pode aceder ao painel e aos endpoints do anfitrião.
- **A prevenção de votos duplicados pode ser contornada usando outro navegador,
  outro perfil, navegação privada, apagando os dados locais ou enviando outro UUID.**
  Não é uma garantia de um voto por pessoa. O backend garante um voto por token e votação.
- O token é partilhado pelas votações na mesma origem do navegador. Alternar entre
  `localhost` e `127.0.0.1` também muda o armazenamento local. Use sempre o mesmo endereço.
- Os resultados são atualizados manualmente; não há WebSockets nem atualização automática.
- As percentagens são arredondadas a uma casa decimal; a soma pode variar ligeiramente de 100%.
- SQLite serve para a demonstração e cargas pequenas. Não se pretende suportar tráfego intenso.
- Não há edição/eliminação de votações, reabertura, autenticação, Docker ou funcionalidades do Nível 3.
- A configuração é de desenvolvimento local (`DEBUG=True` e chave de desenvolvimento),
  não de publicação em produção. Não foram adicionadas dependências de serviços externos.


Com mais tempo, implementaria autenticação para proteger o painel do anfitrião, um sistema mais robusto de identificação dos participantes e atualização automática dos resultados através de WebSockets ou Server-Sent Events.

Para dar Run:
1
cd backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver

2
cd frontend
npm.cmd install
npm.cmd run dev

http://localhost:5173/