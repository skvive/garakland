import { createAuthClient } from 'https://esm.sh/@neondatabase/auth@0.7.0-beta';

let clientPromise;

export async function getAuthClient() {
  if (!clientPromise) {
    clientPromise = fetch('/auth/config.public.json', { cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error('Neon Auth 설정을 읽을 수 없습니다.');
        return r.json();
      })
      .then((cfg) => {
        if (typeof cfg.authUrl !== 'string' || !cfg.authUrl.startsWith('https://')) {
          throw new Error('Neon Auth 주소가 올바르지 않습니다.');
        }
        return createAuthClient(cfg.authUrl);
      })
      .catch((error) => {
        clientPromise = undefined; // Network failures must allow a subsequent retry.
        throw error;
      });
  }
  return clientPromise;
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
