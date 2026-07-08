---
sidebar_position: 4
---

# Credentials

thuis comes with built-in default credentials so you can start downloading immediately. You can also override them with your own VRT MAX account.

## Default credentials

Out of the box, thuis uses these demo credentials:

- **Email:** `kuxelu@ipdeer.com`
- **Password:** `Els123456`

These shared credentials work for basic testing but may have rate limits or access restrictions.

## Using your own account

### Environment variables

Set `VRT_EMAIL` and `VRT_PASSWORD` in your shell:

```bash
export VRT_EMAIL="your-email@example.com"
export VRT_PASSWORD="your-password"
```

### .env file

Create a `.env` file in the project root:

```
VRT_EMAIL=your-email@example.com
VRT_PASSWORD=your-password
```

## Priority order

The tool checks credentials in this order:

1. **Environment variables** — `VRT_EMAIL` and `VRT_PASSWORD` take highest priority
2. **.env file** — loaded via python-dotenv if the package is installed
3. **Built-in defaults** — fallback if nothing else is set
