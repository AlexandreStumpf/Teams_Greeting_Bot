# Teams Greeting Bot 🤖🎵

Bot para Microsoft Teams que automaticamente saúda novos participantes em reuniões com áudio personalizado gerado por IA.

## 🌟 Funcionalidades

- **Detecção Automática**: Identifica quando novos participantes entram em reuniões
- **Saudações Personalizadas**: Gera mensagens "Bom dia [Nome]" customizadas
- **Áudio AI**: Usa OpenAI TTS para criar áudio natural em português
- **Reprodução Automática**: Reproduz o áudio para todos os participantes
- **Multi-idioma**: Suporte para português, inglês, espanhol e francês
- **API REST**: Endpoints para monitoramento e testes

## 🏗️ Arquitetura

```
teams_bot/
├── bot/                    # Handlers do bot Teams
├── config/                 # Configurações e settings
├── models/                 # Modelos Pydantic e schemas
├── routers/               # Rotas FastAPI
├── services/              # Serviços (OpenAI, Teams)
├── main.py               # Aplicação principal
└── requirements.txt      # Dependências
```

## 🚀 Configuração

### 1. Pré-requisitos

- Python 3.9+
- Conta Microsoft Azure
- Chave API OpenAI
- Bot Framework registrado

### 2. Registro do Bot no Azure

1. Acesse o [Azure Portal](https://portal.azure.com)
2. Crie um novo **Azure Bot Service**
3. Configure as seguintes permissões:
   - `Calls.JoinGroupCall.All`
   - `OnlineMeetings.Read.All`
   - `User.Read.All`

### 3. Preparação do Código

```bash
# Clone o repositório
git clone <repo-url>
cd teams_bot

# Instale dependências de desenvolvimento (opcional)
pip install -r requirements.txt
```

### 4. Configuração AWS Lambda

As variáveis de ambiente serão configuradas automaticamente durante o deploy:

- `MICROSOFT_APP_ID` - Bot Framework App ID
- `MICROSOFT_APP_PASSWORD` - Bot Framework Password  
- `MICROSOFT_APP_TENANT_ID` - Azure Tenant ID
- `GRAPH_CLIENT_ID` - Graph API Client ID
- `GRAPH_CLIENT_SECRET` - Graph API Secret
- `OPENAI_API_KEY` - OpenAI API Key
- `BOT_NAME` - Nome do bot (padrão: TeamsGreetingBot)
- `DEFAULT_GREETING_LANGUAGE` - Idioma padrão (padrão: pt-BR)

### 5. Configuração no Teams

1. No Azure Portal, vá para seu Bot Service
2. Em **Configuration**, defina o **Messaging endpoint**:
   
   **Para Lambda:**
   ```
   https://API_GATEWAY_ID.execute-api.REGION.amazonaws.com/STAGE/api/bot/messages
   ```
   
   **Para servidor tradicional:**
   ```
   https://seu-dominio.com/api/bot/messages
   ```
3. Em **Channels**, adicione o canal **Microsoft Teams**
4. Teste a conexão

## 🚀 Deploy no AWS Lambda

### Pré-requisitos
- [AWS CLI](https://aws.amazon.com/cli/) configurado
- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) instalado

```bash
# Instalar SAM CLI
pip install aws-sam-cli

# Configurar credenciais AWS
aws configure
```

### Deploy Automatizado

```bash
# Tornar script executável
chmod +x deploy.sh

# Deploy para desenvolvimento
./deploy.sh dev

# Deploy para produção
./deploy.sh prod
```

### Deploy Manual

```bash
# Build da aplicação
sam build

# Deploy com configuração guiada
sam deploy --guided
```

### Teste Local da Função Lambda

```bash
# Testar função Lambda localmente
python test_lambda_local.py

# Testar API localmente com SAM
sam local start-api
```

## 📡 API Endpoints

### Bot Webhook
- `POST /api/bot/messages` - Webhook principal do Teams

### Monitoramento
- `GET /health` - Health check Lambda
- `GET /api/bot/status` - Status do bot e reuniões ativas
- `GET /api/bot/meetings` - Listar reuniões ativas
- `GET /api/bot/meetings/{id}` - Detalhes de reunião específica

### Testes
- `POST /api/bot/test/greeting` - Testar geração de áudio

### Exemplo de Teste

```bash
# Testar geração de saudação (substituir pela URL real)
curl -X POST "https://API_ID.execute-api.REGION.amazonaws.com/dev/api/bot/test/greeting" \
  -H "Content-Type: application/json" \
  -d '{
    "participant_name": "Alexandre",
    "language": "pt-BR"
  }'
```

## 🎯 Como Usar

### 1. Adicionar o Bot a uma Reunião

1. Abra uma reunião do Teams
2. Clique em **"..."** → **"Aplicativos"**
3. Procure pelo nome do seu bot
4. Adicione à reunião

### 2. Comandos do Bot

No chat da reunião, use:

- `/help` - Mostrar ajuda
- `/status` - Status atual do bot
- `/test Alexandre` - Testar saudação para "Alexandre"

### 3. Funcionamento Automático

Quando o bot está ativo em uma reunião:
1. ✅ Detecta novos participantes automaticamente
2. 🎵 Gera áudio "Bom dia [Nome]" 
3. 📢 Reproduz para todos ouvirem

## 🔧 Configurações Avançadas

### Personalizar Saudações

```python
# Em services/openai_service.py
greetings = {
    "pt-BR": f"Bom dia, {name}! Bem-vindo à reunião",
    "en-US": f"Good morning, {name}! Welcome to the meeting",
    # Adicione mais idiomas...
}
```

### Configurar Vozes

```python
# Mapeamento de vozes por idioma
voice_mapping = {
    "pt-BR": "alloy",    # Boa para português
    "en-US": "echo",     # Boa para inglês
    "es-ES": "fable",    # Boa para espanhol
    "fr-FR": "onyx",     # Boa para francês
}
```

## 🚨 Limitações Importantes

### Reprodução de Áudio

⚠️ **Nota**: A reprodução de áudio em reuniões Teams requer:

1. **Real-time Media Platform**: Capacidades especiais do Bot Framework
2. **Certificação**: Bots que reproduzem áudio precisam ser certificados
3. **Infraestrutura**: Servidores dedicados para streaming de áudio

**Implementação Atual**: O bot gera o áudio mas envia como mensagem de texto por enquanto.

**Para Produção Completa**: 
- Registre o bot para Real-time Media
- Implemente streaming de áudio usando Teams SDK
- Configure infraestrutura adequada

### AWS Lambda Específicas

⚠️ **Limitações do Lambda**:
- **Timeout**: Máximo 15 minutos por execução
- **Armazenamento temporário**: Limitado a `/tmp` (512MB-10GB)
- **Cold Start**: Primeira execução pode ser mais lenta
- **Concorrência**: Limitada por configuração (padrão: 1000)

**Otimizações implementadas**:
- Uso de `/tmp` para arquivos temporários
- AWS Lambda Powertools para observabilidade
- Reutilização de conexões entre invocações
- Configuração de dead letter queue

### Alternativas

- Enviar arquivo de áudio como anexo
- Usar notificações visuais
- Integrar com outros sistemas de áudio
- **Para casos de uso intensivo**: Considere ECS/Fargate

## 🐛 Troubleshooting

### Erros Comuns

1. **Bot não responde**
   - Verifique se o webhook está acessível publicamente
   - Confirme as credenciais do Bot Framework

2. **Erro de autenticação**
   - Valide `MICROSOFT_APP_ID` e `MICROSOFT_APP_PASSWORD`
   - Verifique permissões no Azure

3. **OpenAI API falha**
   - Confirme a chave API válida
   - Verifique limites de uso/billing

4. **Participantes não detectados**
   - Verifique permissões `OnlineMeetings.Read.All`
   - Confirme configuração do Graph API

### Logs

```bash
# Ver logs em tempo real
tail -f app.log

# Logs estruturados em JSON para análise
python -c "import json; [print(json.dumps(json.loads(line), indent=2)) for line in open('app.log')]"
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Siga as diretrizes em `.cursor/rules/GUIDELINES.MD`
4. Faça commit das mudanças
5. Abra um Pull Request

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 🆘 Suporte

Para suporte:
1. Verifique a documentação
2. Consulte os logs da aplicação
3. Abra uma issue no repositório
4. Entre em contato com a equipe de desenvolvimento

---

**Desenvolvido com ❤️ usando FastAPI, Microsoft Bot Framework e OpenAI** 

## 📚 Documentação

- [🚀 **Guia Completo de Deploy**](DEPLOYMENT.md) - Instruções detalhadas para configuração e deploy no AWS Lambda
- [📋 Visão Geral do Projeto](README.md) - Informações gerais e funcionalidades

Para fazer deploy do bot, consulte o [Guia de Deploy](DEPLOYMENT.md) que contém:
- ✅ Passo a passo completo de configuração
- ✅ Como obter todas as credenciais necessárias  
- ✅ Troubleshooting de problemas comuns
- ✅ Monitoramento e manutenção 