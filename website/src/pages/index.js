import React from 'react';
import Layout from '@theme/Layout';

export default function Home() {
  return (
    <Layout title="Thuis Documentation" description="Documentation for Thuis VRT MAX Content Monitor">
      <main style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>Thuis-V2 Documentation</h1>
        <p>Welcome to the Thuis-V2 documentation portal.</p>
        <p>
          <a href="/thuis/intro" style={{ fontSize: '1.2rem', margin: '0 1rem' }}>
            Get Started
          </a>
          <a href="https://github.com/Aldo-f/thuis" style={{ fontSize: '1.2rem', margin: '0 1rem' }}>
            GitHub
          </a>
        </p>
      </main>
    </Layout>
  );
}
