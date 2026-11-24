let clientPromise;

export async function getAuthClient() {
  if (!clientPromise) {
    clientPromise = Promise.all([
      fetch('/auth/config.public.json', { cache: 'no-store' }).then((r) => {
        if (!r.ok) throw new Error('인증 설정을 읽을 수 없습니다.');
        return r.json();
      }),
      import('https://esm.sh/@neondatabase/auth@0.7.0-beta'),
    ]).then(([cfg, sdk]) => sdk.createAuthClient(cfg.authUrl))
      .catch((err) => { clientPromise = null; throw err; });
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
