# YouTube Playlist Creator

Cria e sincroniza playlists do YouTube a partir de arquivos Markdown.

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Configuração do Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a **YouTube Data API v3**
4. Configure a tela de consentimento OAuth:
   - User Type: Externo
   - Adicione seu email como usuário de teste
5. Crie credenciais OAuth 2.0 (tipo: Aplicativo Desktop)
6. Baixe o arquivo JSON e salve como `client_secrets.json` na raiz do projeto

## Uso

### Formato do arquivo Markdown

```markdown
# Nome da Playlist

| # | Música | Artista |
|---|--------|---------|
| 1 | Yeah! | Usher ft. Lil Jon & Ludacris |
| 2 | In Da Club | 50 Cent |
```

### Comandos

```bash
# Buscar músicas (salva no cache)
python main.py search playlist.md

# Criar playlist nova
python main.py create playlist.md

# Criar com nome customizado
python main.py create playlist.md --name "Minha Playlist"

# Sincronizar playlist existente
python main.py sync playlist.md --playlist-url "https://youtube.com/playlist?list=PLxxxxx"

# Ver o que seria feito (dry-run)
python main.py create playlist.md --dry-run
python main.py sync playlist.md --playlist-id PLxxxxx --dry-run
```

### Opções

| Comando | Opção | Descrição |
|---------|-------|-----------|
| search | --force | Re-buscar músicas já no cache |
| search | --verbose | Mostrar detalhes das buscas |
| create | --name | Nome customizado da playlist |
| create | --dry-run | Simular sem criar |
| create | --skip-missing | Pular músicas não encontradas sem confirmar |
| sync | --playlist-url | URL da playlist do YouTube |
| sync | --playlist-id | ID da playlist |
| sync | --remove-unknown | Remover músicas não mapeadas |
| sync | --dry-run | Simular sem modificar |

## Cache

O cache fica em `~/.youtube-playlist-cache/searches.json`.

Você pode editar manualmente para:
- Mudar o vídeo selecionado (campo `selected`)
- Adicionar um `video_id` para músicas não encontradas

## Limites da API

- Quota diária: 10.000 unidades
- Busca: 100 unidades
- Adicionar vídeo: 50 unidades

Uma playlist de 50 músicas usa ~7.500 unidades.

## Licença

MIT
