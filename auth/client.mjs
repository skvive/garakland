import { createAuthClient } from 'https://esm.sh/@neondatabase/neon-js@1/auth';

let clientPromise;

export async function getAuthClient() {
  if (!clientPromise) {
    clientPromise = fetch('/auth/config.public.json', { cache: 'no-store' })
      .then((r) => r.json())
      .then((cfg) => createAuthClient(cfg.authUrl));
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
