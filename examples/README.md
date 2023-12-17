# Chalice-spec project sample

## Setup

- Install Docker (e.g. wsl)
- Create `.env` file in this directory.  
  format:: `.env_template`

Execute build-script, build docker image.

```bash
./1.build-script.sh
```

## Execute local

Execute script, start local server.

```bash
./2.run-local-api-apigateway-en.sh
```

## Deploy with API Gateway

Create AWS Resources, and deploy chalice.  
You can execute api with HTTPS.

```bash
./3.deploy-api-gateway-en.sh
```

## Deploy with Agents for Amazon Bedrock

Setup:

- Enable bedrock model access (Anthropic Claude).

Create AWS Resources, and deploy chalice.

```bash
./b.3.deploy-agent-for-amazon-bedrock.sh
```

Connect amazon bedrock with chalice.  
You can execute api with natural language.

```bash
./b.4.init-agent-for-amazon-bedrock.sh
```

If you want to update api schema.

```bash
./b.5.sync-agent-for-amazon-bedrock.sh
```

## Clean

```bash
## When created with "Deploy with API Gateway"
./9.delete-api-gateway-en.sh
## When created with "Deploy with Agents for Amazon Bedrock"
./b.9.delete-agent-for-amazon-bedrock.sh
```
