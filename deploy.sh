#!/bin/bash

# Teams Greeting Bot - AWS Lambda Deployment Script
# Usage: ./deploy.sh [environment] [profile]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-dev}
AWS_PROFILE=${2:-default}
STACK_NAME="teams-greeting-bot"

if [ "$ENVIRONMENT" = "prod" ]; then
    STACK_NAME="teams-greeting-bot-prod"
fi

echo -e "${BLUE}🚀 Deploying Teams Greeting Bot to AWS Lambda${NC}"
echo -e "${BLUE}Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "${BLUE}AWS Profile: ${YELLOW}$AWS_PROFILE${NC}"
echo -e "${BLUE}Stack Name: ${YELLOW}$STACK_NAME${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}Install with: pip install aws-sam-cli${NC}"
    exit 1
fi

# Validate AWS credentials
echo -e "${BLUE}🔐 Validating AWS credentials...${NC}"
if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
    echo -e "${RED}❌ Invalid AWS credentials for profile: $AWS_PROFILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS credentials validated${NC}"

# Check if .env file exists for local testing
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << EOF
# Microsoft Bot Framework
MICROSOFT_APP_ID=your_bot_app_id
MICROSOFT_APP_PASSWORD=your_bot_password
MICROSOFT_APP_TENANT_ID=your_tenant_id

# Microsoft Graph API
GRAPH_CLIENT_ID=your_graph_client_id
GRAPH_CLIENT_SECRET=your_graph_client_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Local development only
HOST=0.0.0.0
PORT=8000
DEBUG=true
BOT_NAME=TeamsGreetingBot
DEFAULT_GREETING_LANGUAGE=pt-BR
EOF
    echo -e "${YELLOW}Please update .env file with your actual values${NC}"
fi

# Prompt for required parameters if not set
echo -e "${BLUE}📝 Checking deployment parameters...${NC}"

if [ -z "$MICROSOFT_APP_ID" ]; then
    read -p "Enter Microsoft App ID: " MICROSOFT_APP_ID
fi

if [ -z "$MICROSOFT_APP_PASSWORD" ]; then
    read -s -p "Enter Microsoft App Password: " MICROSOFT_APP_PASSWORD
    echo ""
fi

if [ -z "$MICROSOFT_APP_TENANT_ID" ]; then
    read -p "Enter Microsoft Tenant ID: " MICROSOFT_APP_TENANT_ID
fi

if [ -z "$GRAPH_CLIENT_ID" ]; then
    read -p "Enter Graph Client ID: " GRAPH_CLIENT_ID
fi

if [ -z "$GRAPH_CLIENT_SECRET" ]; then
    read -s -p "Enter Graph Client Secret: " GRAPH_CLIENT_SECRET
    echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
    read -s -p "Enter OpenAI API Key: " OPENAI_API_KEY
    echo ""
fi

# Build the application
echo -e "${BLUE}🔨 Building application...${NC}"
sam build --profile $AWS_PROFILE

# Validate the template
echo -e "${BLUE}✅ Validating SAM template...${NC}"
sam validate --profile $AWS_PROFILE

# Deploy the application
echo -e "${BLUE}🚀 Deploying to AWS...${NC}"
sam deploy \
    --profile $AWS_PROFILE \
    --config-env $ENVIRONMENT \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        MicrosoftAppId="$MICROSOFT_APP_ID" \
        MicrosoftAppPassword="$MICROSOFT_APP_PASSWORD" \
        MicrosoftAppTenantId="$MICROSOFT_APP_TENANT_ID" \
        GraphClientId="$GRAPH_CLIENT_ID" \
        GraphClientSecret="$GRAPH_CLIENT_SECRET" \
        OpenAIApiKey="$OPENAI_API_KEY" \
    --capabilities CAPABILITY_IAM \
    --stack-name $STACK_NAME

# Get outputs
echo -e "${BLUE}📋 Getting deployment outputs...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text \
    --profile $AWS_PROFILE)

WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`BotWebhookUrl`].OutputValue' \
    --output text \
    --profile $AWS_PROFILE)

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' \
    --output text \
    --profile $AWS_PROFILE)

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📱 API Gateway URL:${NC} $API_URL"
echo -e "${BLUE}🤖 Bot Webhook URL:${NC} $WEBHOOK_URL"
echo -e "${BLUE}⚡ Lambda Function:${NC} $LAMBDA_ARN"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo -e "1. Update your Microsoft Bot Framework messaging endpoint to:"
echo -e "   ${WEBHOOK_URL}"
echo -e "2. Test the health endpoint:"
echo -e "   curl ${API_URL}/health"
echo -e "3. Test greeting generation:"
echo -e "   curl -X POST ${API_URL}/api/bot/test/greeting \\"
echo -e "     -H 'Content-Type: application/json' \\"
echo -e "     -d '{\"participant_name\": \"Alexandre\", \"language\": \"pt-BR\"}'"
echo ""

# Test the deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"
if curl -f -s "${API_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
fi

echo -e "${GREEN}🚀 Deployment script completed!${NC}" 