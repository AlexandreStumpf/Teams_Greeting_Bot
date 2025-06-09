# Guia de Deploy e Configuração - Teams Bot

Este guia contém todas as instruções necessárias para configurar e fazer o deploy do Teams Bot na AWS Lambda.

## 📋 Pré-requisitos

### 1. Ferramentas Necessárias

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# AWS SAM CLI
brew install aws-sam-cli

# Python 3.9+
python3 --version
```

### 2. Configuração AWS

```bash
# Configure suas credenciais AWS
aws configure
```

## 🔑 Configuração de Credenciais

### 1. Microsoft Bot Framework

#### Obter App ID e App Secret

1. Acesse o [Azure Portal](https://portal.azure.com)
2. Navegue até **Azure Active Directory** > **App registrations**
3. Clique em **New registration**
4. Preencha:
   - **Name**: `teams-greeting-bot`
   - **Supported account types**: Multitenant
   - **Redirect URI**: Deixe em branco
5. Clique **Register**
6. Anote o **Application (client) ID** (será o `MICROSOFT_APP_ID`)
7. Vá para **Certificates & secrets** > **Client secrets** > **New client secret**
8. Adicione uma descrição e defina expiração
9. Copie o **Value** (será o `MICROSOFT_APP_PASSWORD`)

#### Configurar Permissões

1. No app registration, vá para **API permissions**
2. Clique **Add a permission** > **Microsoft Graph** > **Application permissions**
3. Adicione as seguintes permissões:
   - `Calls.Initiate.All`
   - `Calls.InitiateGroupCall.All`
   - `Calls.JoinGroupCall.All`
   - `Calls.JoinGroupCallAsGuest.All`
   - `OnlineMeetings.Read.All`
   - `OnlineMeetings.ReadWrite.All`
4. Clique **Grant admin consent**

### 2. Microsoft Graph API

#### Registrar Bot no Bot Framework

1. Acesse [Bot Framework Portal](https://dev.botframework.com)
2. Clique **Create a Bot** > **Register an existing bot built elsewhere**
3. Preencha:
   - **Bot handle**: Nome único para seu bot
   - **Microsoft App ID**: Use o ID criado anteriormente
   - **Messaging endpoint**: `https://sua-lambda-url.execute-api.region.amazonaws.com/messages`
4. Configure o canal Microsoft Teams

### 3. OpenAI API

1. Acesse [OpenAI Platform](https://platform.openai.com)
2. Vá para **API Keys**
3. Clique **Create new secret key**
4. Copie a chave (será o `OPENAI_API_KEY`)

## 🚀 Opções de Deploy

### Opção 1: Deploy Automatizado (Recomendado)

```bash
# Torna o script executável
chmod +x deploy.sh

# Executa o deploy automatizado
./deploy.sh
```

O script irá solicitar as credenciais necessárias e fazer o deploy completo.

### Opção 2: Variáveis de Ambiente + SAM

```bash
# Configure as variáveis de ambiente
export MICROSOFT_APP_ID="sua-app-id"
export MICROSOFT_APP_PASSWORD="sua-app-password"
export MICROSOFT_TENANT_ID="sua-tenant-id"
export OPENAI_API_KEY="sua-openai-key"

# Faça o build e deploy
sam build
sam deploy --guided
```

### Opção 3: Deploy Manual

```bash
# Build da aplicação
sam build

# Deploy interativo
sam deploy \
  --parameter-overrides \
    ParameterKey=MicrosoftAppId,ParameterValue=sua-app-id \
    ParameterKey=MicrosoftAppPassword,ParameterValue=sua-app-password \
    ParameterKey=MicrosoftTenantId,ParameterValue=sua-tenant-id \
    ParameterKey=OpenAIApiKey,ParameterValue=sua-openai-key \
  --capabilities CAPABILITY_IAM \
  --stack-name teams-greeting-bot
```

## 📝 Configuração das Variáveis

### Variáveis Obrigatórias

| Variável | Descrição | Como Obter |
|----------|-----------|------------|
| `MICROSOFT_APP_ID` | ID da aplicação Azure | Azure Portal > App registrations |
| `MICROSOFT_APP_PASSWORD` | Secret da aplicação | Azure Portal > Certificates & secrets |
| `MICROSOFT_TENANT_ID` | ID do tenant Azure | Azure Portal > Azure Active Directory |
| `OPENAI_API_KEY` | Chave da API OpenAI | OpenAI Platform > API Keys |

### Variáveis Opcionais

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `LOG_LEVEL` | Nível de log | `INFO` |
| `ENVIRONMENT` | Ambiente de execução | `production` |
| `OPENAI_MODEL` | Modelo de TTS | `tts-1` |
| `OPENAI_VOICE` | Voz para TTS | `alloy` |

## ✅ Verificação do Deploy

### 1. Verificar Stack AWS

```bash
# Listar stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE

# Verificar recursos da stack
aws cloudformation describe-stack-resources --stack-name teams-greeting-bot
```

### 2. Testar Lambda Function

```bash
# Obter URL da API
aws cloudformation describe-stacks \
  --stack-name teams-greeting-bot \
  --query 'Stacks[0].Outputs[?OutputKey==`TeamsGreetingBotApi`].OutputValue' \
  --output text
```

### 3. Teste Local (Opcional)

```bash
# Configurar variáveis locais
export MICROSOFT_APP_ID="sua-app-id"
export MICROSOFT_APP_PASSWORD="sua-app-password"
export MICROSOFT_TENANT_ID="sua-tenant-id"
export OPENAI_API_KEY="sua-openai-key"

# Executar teste local
python test_lambda_local.py
```

## 🔧 Configuração do Bot no Teams

### 1. Atualizar Endpoint do Bot

1. Acesse [Bot Framework Portal](https://dev.botframework.com)
2. Selecione seu bot
3. Vá para **Settings**
4. Atualize **Messaging endpoint** com a URL da sua Lambda:
   ```
   https://sua-lambda-url.execute-api.region.amazonaws.com/messages
   ```

### 2. Configurar Manifest do Teams

Crie um arquivo `manifest.json`:

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "SEU_MICROSOFT_APP_ID",
  "packageName": "com.teams.greetingbot",
  "developer": {
    "name": "Sua Empresa",
    "websiteUrl": "https://sua-empresa.com",
    "privacyUrl": "https://sua-empresa.com/privacy",
    "termsOfUseUrl": "https://sua-empresa.com/terms"
  },
  "icons": {
    "color": "icon-color.png",
    "outline": "icon-outline.png"
  },
  "name": {
    "short": "Greeting Bot",
    "full": "Teams Greeting Bot"
  },
  "description": {
    "short": "Bot que cumprimenta participantes",
    "full": "Bot que gera cumprimentos personalizados para participantes de reuniões"
  },
  "accentColor": "#FFFFFF",
  "bots": [
    {
      "botId": "SEU_MICROSOFT_APP_ID",
      "scopes": ["team", "personal", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": []
}
```

## 📊 Monitoramento

### CloudWatch Logs

```bash
# Visualizar logs da função Lambda
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/teams-greeting-bot"

# Visualizar logs em tempo real
aws logs tail "/aws/lambda/teams-greeting-bot-TeamsGreetingBotFunction" --follow
```

### Métricas

- **Invocations**: Número de execuções
- **Duration**: Tempo de execução
- **Errors**: Número de erros
- **Throttles**: Execuções limitadas

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Autenticação

```
Error: Failed to authenticate with Microsoft Graph
```

**Solução**:
- Verificar se `MICROSOFT_APP_ID` e `MICROSOFT_APP_PASSWORD` estão corretos
- Confirmar que as permissões foram concedidas no Azure Portal
- Verificar se o tenant ID está correto

#### 2. Erro de Permissões

```
Error: Insufficient privileges to complete the operation
```

**Solução**:
- Adicionar permissões necessárias no Azure Portal
- Executar "Grant admin consent" para as permissões
- Aguardar alguns minutos para propagação

#### 3. Timeout na Lambda

```
Error: Task timed out after 30.00 seconds
```

**Solução**:
- Aumentar timeout na configuração do SAM template
- Otimizar código para reduzir tempo de execução
- Verificar conectividade com APIs externas

#### 4. Erro OpenAI API

```
Error: OpenAI API key is invalid
```

**Solução**:
- Verificar se a chave da API está correta
- Confirmar que há créditos disponíveis na conta OpenAI
- Verificar limites de rate limiting

### Logs Detalhados

Para debug avançado, configure `LOG_LEVEL=DEBUG`:

```bash
# Atualizar variável de ambiente
aws lambda update-function-configuration \
  --function-name teams-greeting-bot-TeamsGreetingBotFunction \
  --environment Variables='{
    "LOG_LEVEL":"DEBUG",
    "MICROSOFT_APP_ID":"sua-app-id",
    "MICROSOFT_APP_PASSWORD":"sua-app-password",
    "MICROSOFT_TENANT_ID":"sua-tenant-id",
    "OPENAI_API_KEY":"sua-openai-key"
  }'
```

## 🔄 Atualizações

### Deploy de Nova Versão

```bash
# Fazer build e deploy
sam build && sam deploy
```

### Rollback

```bash
# Listar versões
aws lambda list-versions-by-function --function-name teams-greeting-bot-TeamsGreetingBotFunction

# Fazer rollback para versão anterior
aws lambda update-alias \
  --function-name teams-greeting-bot-TeamsGreetingBotFunction \
  --name LIVE \
  --function-version VERSAO_ANTERIOR
```

## 🔐 Segurança

### Práticas Recomendadas

1. **Rotação de Secrets**: Rotacione regularmente as chaves da API
2. **Least Privilege**: Use apenas as permissões mínimas necessárias
3. **Encryption**: Todas as variáveis sensíveis são criptografadas
4. **Monitoring**: Configure alertas para tentativas de acesso não autorizadas

### AWS Secrets Manager (Opcional)

Para maior segurança, você pode armazenar secrets no AWS Secrets Manager:

```bash
# Criar secret
aws secretsmanager create-secret \
  --name teams-bot-secrets \
  --secret-string '{
    "MICROSOFT_APP_PASSWORD":"sua-app-password",
    "OPENAI_API_KEY":"sua-openai-key"
  }'
```

## 📞 Suporte

### Recursos Úteis

- [Documentação Bot Framework](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

### Logs de Debug

Para investigar problemas:

```bash
# Exportar logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/teams-greeting-bot-TeamsGreetingBotFunction" \
  --start-time $(date -d "1 hour ago" +%s)000 \
  --query 'events[*].message' \
  --output text
```

## ✅ Checklist Final

- [ ] Credenciais AWS configuradas
- [ ] App registration criado no Azure
- [ ] Permissões concedidas no Azure Portal
- [ ] Bot registrado no Bot Framework
- [ ] Chave OpenAI obtida
- [ ] Deploy realizado com sucesso
- [ ] URL do webhook atualizada no Bot Framework
- [ ] Teste de funcionalidade realizado
- [ ] Monitoramento configurado
- [ ] Documentação revisada

---

🎉 **Parabéns!** Seu Teams Greeting Bot está agora rodando na AWS Lambda! 