import { describe, expect, it } from 'vitest';
import { localDiagnosticsEnabled } from '../domain/local-diagnostics';

const authorized = {
  pageUrl: 'http://localhost:8081/app/recognition?diagnostics=1',
  apiBaseUrl: '', developmentBuild: false, localDiagnosticsFlag: 'true',
  token: 'local-colors-diagnostic-token-only',
};

describe('local diagnostics authorization conditions', () => {
  it('allows the explicitly configured local Docker build and development build', () => {
    expect(localDiagnosticsEnabled(authorized)).toBe(true);
    expect(localDiagnosticsEnabled({ ...authorized, developmentBuild: true, localDiagnosticsFlag: 'false' })).toBe(true);
    expect(localDiagnosticsEnabled({ ...authorized, pageUrl: 'http://127.0.0.1:8081/?diagnostics=1' })).toBe(true);
    expect(localDiagnosticsEnabled({ ...authorized, pageUrl: 'http://[::1]:8081/?diagnostics=1' })).toBe(true);
  });
  it.each([
    { localDiagnosticsFlag: 'false' },
    { localDiagnosticsFlag: undefined },
    { token: '' },
    { token: 'short' },
    { pageUrl: 'http://localhost:8081/app/recognition' },
    { pageUrl: 'http://localhost:8081/?diagnostics=0' },
    { pageUrl: 'http://example.com/?diagnostics=1' },
    { pageUrl: 'http://localhost.example.com/?diagnostics=1' },
    { apiBaseUrl: 'https://example.com' },
    { apiBaseUrl: 'http://localhost:8082' },
    { pageUrl: 'not a url' },
  ])('fails closed when authorization condition is missing: %o', (change) => {
    expect(localDiagnosticsEnabled({ ...authorized, ...change })).toBe(false);
  });
});
