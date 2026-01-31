---
name: 1password
description: Manage credentials, secrets, vaults, tokens and secure storage using 1password using the op CLI. Use when (1) Retrieving or setting passwords, API keys, and secrets from vaults, (2) Injecting secrets into environment variables and config files, (3) Automating credential rotation and management, (4) Accessing SSH keys and certificates, (5) Doing CRUD operations on vaults and secure items.
---

# 1Password CLI Skill

Use 1Password for secure secret management.

## Authentication

You are pre-authenticated using environment variables. Check using `op whoami`:

Good:
```bash
$ op whoami
URL:               https://my.1password.eu
Integration ID:    XXXXXXXXXXXXXXXXXXXXXXXXX
User Type:         SERVICE_ACCOUNT
```

If User Type is not SERVICE_ACCOUNT, ask the user to fix your environment and stop.

You MUST NOT try to sign in, sign out, connect, or use a different account. If you think you need a different account, instead ask the user for help and stop.

## Vaults

Your service account has access to read and write to one vault named "AI". This is where all your secrets go.

Good:
```bash
$ op vault list
ID                            NAME
idxxxxxxxxxxxxxxxxxxxxxxxx    AI
```

You can pass the vault ID "AI" to other commands that need it. For example:

Good:
```bash
op item list --vault AI
```

## Items

Items are stored inside vaults and can be passwords, login credentials, API tokens, SSH keys, and more.

### Retrieving items

```bash
# List all items
op item list

# Get complete item details
op item get <item-name-or-id>
op item get "GitHub Token"
op item get "AWS Credentials"

# Get item in JSON format
op item get "GitHub Token" --format json
```

### Retrieving specific fields

```bash
# Get a specific field value
op item get <item-name> --fields <field-name>

# Examples
op item get "GitHub Token" --fields token
op item get "AWS Credentials" --fields "access key"

# Get multiple fields as JSON
op item get "AWS Credentials" --fields "access key,secret key" --format json

# Using field notation (for scripting)
op read "op://<vault>/<item>/<field>"
op read "op://AI/GitHub Token/token"
op read "op://AI/AWS Credentials/access key"
```

### Creating and updating items

```bash
# Create a new login item
op item create --category Login \
  --title "New Service" \
  --vault "Private" \
  --url "https://example.com" \
  username=user@example.com \
  password=<generate-password>

# Create item with custom fields
op item create --category Password \
  --title "API Key" \
  --vault "Work" \
  api_key=sk-xxx \
  environment=production

# Create secure note
op item create --category "Secure Note" \
  --title "Deployment Notes" \
  --vault "Work" \
  notesPlain="Important deployment information"

# Update an existing item
op item edit <item-name> <field>=<value>
op item edit "GitHub Token" token=ghp_newtoken123

# Add tags to item
op item edit "AWS Credentials" --tags production,terraform

# Generate and update password
op item edit "Database Login" password=<generate-password>
```

## Deleting items

Do not delete items from 1Password. If you think you must delete items, ask the user for help and stop.

## Secret references

Use secret references to inject 1Password secrets into applications without exposing them:

```
# Secret reference syntax
op://[vault]/[item]/[field]

# Examples
op://Private/GitHub Token/token
op://Work/AWS Credentials/access key
op://DevOps/Database/password
```

```
# Using op run to inject secrets into commands
op run -- env
op run -- npm run build
op run -- terraform apply

# Using op inject with templates
echo 'DB_PASSWORD=op://Work/Database/password' | op inject
cat .env.template | op inject > .env
```

## Getting help

For more information on these commands, run `op --help`. Pass `--help` to a subcommand for more instructions. For example:

```bash
op vault --help
op vault list --help
op item --help
op item list --help
op item get --help
op run --help
```
