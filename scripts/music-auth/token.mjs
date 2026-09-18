const encode = (bytes) => btoa(String.fromCharCode(...bytes))
  .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
const json = (value) => encode(new TextEncoder().encode(JSON.stringify(value)));
export class SetupError extends Error {}
const cryptoError = (step, error) => new SetupError(`${step} failed (${['DataError', 'NotSupportedError', 'OperationError', 'InvalidAccessError', 'TypeError'].includes(error?.name) ? error.name : 'Error'}). Try this setup page in Chrome if Safari cannot import or sign with this key.`);

export async function developerToken(teamId, keyId, pem) {
  if (!/^[A-Z0-9]{10}$/.test(teamId) || !/^[A-Z0-9]{10}$/.test(keyId)) {
    throw new SetupError('Team ID and Key ID must each contain 10 uppercase letters or digits.');
  }
  if (!pem.includes('-----BEGIN PRIVATE KEY-----')) {
    throw new SetupError('The key must include the BEGIN PRIVATE KEY header. Select the Apple .p8 file or paste its complete contents.');
  }
  if (!globalThis.crypto?.subtle) {
    throw new SetupError('Web Crypto is unavailable in this browser context. Open http://localhost:8765 in Safari, or use Chrome on this Mac.');
  }
  let bytes;
  try {
    bytes = Uint8Array.from(atob(pem.replace(/-----[\w ]+-----/g, '').replace(/\s/g, '')), c => c.charCodeAt(0));
  } catch {
    throw new SetupError('The private key contains invalid base64. Select the original .p8 file or paste its complete contents.');
  }
  let key;
  try {
    key = await crypto.subtle.importKey('pkcs8', bytes,
      { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  } catch (error) { throw cryptoError('P-256 private-key import', error); }
  const now = Math.floor(Date.now() / 1000);
  const body = `${json({ alg: 'ES256', kid: keyId })}.${json({ iss: teamId, iat: now - 30, exp: now + 3600 })}`;
  let signature;
  try {
    signature = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key,
      new TextEncoder().encode(body));
  } catch (error) { throw cryptoError('Developer-token signing', error); }
  return `${body}.${encode(new Uint8Array(signature))}`;
}
