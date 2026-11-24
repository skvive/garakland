import { getAuthClient, getSession, signOut } from './client.mjs';

export async function getMemberSession() {
  return await getSession();
}

async function accessToken() {
  const auth = await getAuthClient();
  // Neon Auth exposes its signed JWT through the JWT plugin or getJWTToken.
  if (typeof auth.token === 'function') {
    const result = await auth.token();
    const token = result?.data?.token || result?.data?.access_token || result?.token;
    if (typeof token === 'string' && token.split('.').length === 3) return token;
  }
  if (typeof auth.getJWTToken === 'function') {
    const token = await auth.getJWTToken();
    if (typeof token === 'string' && token.split('.').length === 3) return token;
  }
  const current = await getSession();
  const token = current?.session?.access_token;
  if (typeof token === 'string' && token.split('.').length === 3) return token;
  throw new Error('로그인 토큰을 확인할 수 없습니다. 다시 로그인해 주세요.');
}

export async function memberRequest(path, data = null) {
  if (!/^\/api\/member\/(?:state|favorites|coupons)$/.test(path)) {
    throw new Error('허용되지 않은 회원 API 경로입니다.');
  }
  const session = await getSession();
  if (!session?.user?.id) throw new Error('로그인이 필요합니다.');
  const token = await accessToken();
  const response = await fetch(path, {
    method: data === null ? 'GET' : 'POST',
    cache: 'no-store',
    credentials: 'same-origin',
    headers: {
      Authorization: 'Bearer ' + token,
      'X-Garak-Client': '1',
      ...(data !== null ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(data !== null ? { body: JSON.stringify(data) } : {}),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || '회원 데이터 저장에 실패했습니다.');
  return result;
}

export { signOut };
