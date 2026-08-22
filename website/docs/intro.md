---
id: intro
title: Introduction
sidebar_position: 1
---

# Introduction

Welcome to the **Thuis v5** documentation portal.

Thuis is a high-precision, modular ecosystem engineered to monitor and manage media references from VRT MAX, specifically focusing on the popular Belgian television series **"Thuis"**.

## Core Vision

Thuis v5 is built as a single monorepo powering both responsive web and native desktop applications from a shared business logic library.

- **Monorepo (pnpm Workspaces)**: Code is logically separated into reusable packages under `packages/*` and the `website/` portal.
- **Single Source of Truth**: The `@thuis/core` package encapsulates all VRT MAX API communications, schema validations, and state.
- **Strict Type Safety**: All inputs, outputs, and storage states are parsed and strictly validated using **Zod** schemas.
- **Zustand State Engine**: Highly optimized, reactive global state slices with seamless persistence capabilities.

## Portals & Apps

- **Core Library**: Shared business logic, GraphQL API client, URL resolver, Zod schemas, and combined state.
- **Web App**: Responsive Single Page Application (SPA) built with React 19, Vite, and Tailwind 4.
- **Electron App**: Native multi-platform desktop shell (Electron 31) with secure IPC contexts, native file system integration, and automatic updates.
- **Docs Portal**: You are currently reading the Docusaurus documentation portal.
