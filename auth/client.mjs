let clientPromise;

function looksLikeJWT(token) {
  return typeof token === 'string' && token.split('.').length === 3;
}
async function makeClientBundle() {
  const response = await fetch('/auth/config.public.json', { cache: 'no-store' });
  if (!response.ok) throw new Error('인증 설정을 읽을 수 없습니다.');
  const cfg = await response.json();
  const sdk = await import('https://esm.sh/@neondatabase/auth@0.7.0-beta');
  // Neon Auth wrapper exposes the managed JWT retriever while keeping the
  // same Better Auth client for social sign-in and session checks.
  const managed = typeof sdk.createInternalNeonAuth === 'function'
    ? sdk.createInternalNeonAuth(cfg.authUrl)
    : null;
  return {
    auth: managed?.adapter || sdk.createAuthClient(cfg.authUrl),
    getJWT: managed?.getJWTToken ? () => managed.getJWTToken() : null,
  };
}
async function bundle() {
  if (!clientPromise) {
    clientPromise = makeClientBundle().catch(err => {
      clientPromise = null;
      throw err;
    });
  }
  return clientPromise;
}
export async function getAuthClient() {
  return (await bundle()).auth;
}
export async function getMemberJWT() {
  const { auth, getJWT } = await bundle();
  const sessionResult = await auth.getSession();
  const data = sessionResult?.data ?? sessionResult;
  if (!data?.user?.id) throw new Error('로그인된 계정을 확인할 수 없습니다.');
  // Neon SDK's managed JWT (EdDSA) is different from the opaque session token.
  if (getJWT) {
    const token = await getJWT();
    if (looksLikeJWT(token)) return token;
  }
  if (typeof auth.getJWTToken === 'function') {
    const token = await auth.getJWTToken();
    if (looksLikeJWT(token)) return token;
  }
  const token = data.session?.access_token;
  if (looksLikeJWT(token)) return token;
  throw new Error('회원 인증 토큰을 발급받지 못했습니다. 다시 로그인해 주세요.');
}
export async function getSession() {
  const auth = await getAuthClient();
  const result = await auth.getSession();
  return result.data ?? null;
}

export async function signOut() {
  const auth = await getAuthClient();
  await auth.signOut();
}

export async function signInWithGoogle(callbackURL) {
  const auth = await getAuthClient();
  const origin = window.location.origin;
  return auth.signIn.social({
    provider: 'google',
    callbackURL: callbackURL || `${origin}/login.html`,
    errorCallbackURL: `${origin}/login.html?error=oauth`,
  });
}
