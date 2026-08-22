---
id: usage
title: Usage & MVP Guide
sidebar_position: 4
---

# Usage & MVP Guide

This guide walks you through the primary Minimum Viable Product (MVP) workflow of the Thuis v5 portal.

## The MVP Workflow

The MVP focuses on resolving and downloading a specific "Thuis" episode from a VRT MAX URL:

`https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6102/`

### 1. Paste Episode URL
Navigate to the Web App or Electron App home screen and paste the target VRT MAX URL into the resolve input field.

### 2. Metadata Hydration
The `parseVrtUrl` resolver parses the URL to extract show components. The GraphQL client queries VRT MAX, validates the returned payload with Zod schemas, and populates the Zustand store.

### 3. Queue Download
Click **Download Episode**. The download service enqueues the job (`status: "pending"`), resolves the video manifest through the Vualto Video Aggregator, and streams the media segments locally.
