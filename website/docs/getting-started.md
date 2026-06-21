---
id: getting-started
title: Getting Started
sidebar_position: 2
---

# Getting Started

Follow this guide to set up the Thuis monorepo locally and begin development.

## Prerequisites

Ensure you have the following software installed:
- **Node.js** >= 20.x
- **pnpm** >= 10.x (Workspace package manager)
- **git**

## Installation

Clone the repository and install all workspace dependencies:

```bash
git clone https://github.com/Aldo-f/thuis.git
cd thuis
pnpm install
```

## Running the Applications

The workspace contains script aliases configured in the root `package.json` for running the packages.

### Web Application

To run the React web-app dev server locally:

```bash
pnpm --filter @thuis/web-app dev
```

The web-app will be available at `http://localhost:5173`.

### Electron Application

To start the Electron desktop application with hot-reloading (make sure the Web dev server is running first):

```bash
NODE_ENV=development pnpm --filter @thuis/electron-app dev
```

### Documentation Site

To preview this documentation portal locally:

```bash
cd website
pnpm install --no-frozen-lockfile
pnpm start
```
