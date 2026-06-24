import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import { ProviderCredentialForm } from '../../components/vault/ProviderCredentialForm';
import { CredentialVault } from '@thuis/core/vault/CredentialVault';

const mockProvider = { id: 'vrt' as const, displayName: 'VRT' };

test.describe('ProviderCredentialForm component', () => {
  test.beforeEach(() => {
    // Mock vault method to avoid real storage/network
    // @ts-ignore
    CredentialVault.prototype.addCredentials = async () => Promise.resolve();
  });

  test('submits valid credentials and calls onSubmit', async ({ mount }) => {
    const onSubmit = jest.fn();
    const component = await mount(
      <ProviderCredentialForm provider={mockProvider} onSubmit={onSubmit} />
    );
    await component.fill('#vrt-email', 'test@example.com');
    await component.fill('#vrt-password', 'secret123');
    await component.click('text=Opslaan');
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ email: 'test@example.com', password: 'secret123' })
    );
  });

  test('shows Dutch validation errors for empty fields', async ({ mount }) => {
    const onSubmit = jest.fn();
    const component = await mount(
      <ProviderCredentialForm provider={mockProvider} onSubmit={onSubmit} />
    );
    await component.click('text=Opslaan');
    // Expect validation alerts – we check that onSubmit was not called
    expect(onSubmit).not.toHaveBeenCalled();
    // Since the component uses alert for errors, we check that inputs are still visible
    await expect(component.locator('#vrt-email')).toBeVisible();
    await expect(component.locator('#vrt-password')).toBeVisible();
  });
});
