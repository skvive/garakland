import { getSession, getMemberJWT, signOut } from './client.mjs';

export async function getMemberSession() {
  return await getSession();
}


export async function memberRequest(path, data = null) {
  if (!/^\/api\/member\/(?:state|favorites|coupons)$/.test(path)) {
    throw new Error('허용되지 않은 회원 API 경로입니다.');
  }
  const session = await getSession();
  if (!session?.user?.id) throw new Error('로그인이 필요합니다.');
  const token = await getMemberJWT();
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
