/** Local diagnostics are an opt-in development feature, never an authentication mechanism. */
export function isLocalSameOrigin(pageUrl: string, apiBaseUrl: string): boolean {
  try {
    const page = new URL(pageUrl);
    const api = new URL(apiBaseUrl || page.origin, page.origin);
    return ['localhost', '127.0.0.1', '[::1]'].includes(page.hostname) && api.origin === page.origin;
  } catch {
    return false;
  }
}

export function localDiagnosticsEnabled(options: {
  pageUrl: string;
  apiBaseUrl: string;
  developmentBuild: boolean;
  localDiagnosticsFlag: string | undefined;
  token: string;
}): boolean {
  const { pageUrl, apiBaseUrl, developmentBuild, localDiagnosticsFlag, token } = options;
  try {
    return (developmentBuild || localDiagnosticsFlag === 'true') &&
      isLocalSameOrigin(pageUrl, apiBaseUrl) && token.length >= 16 &&
      new URL(pageUrl).searchParams.get('diagnostics') === '1';
  } catch {
    return false;
  }
}
