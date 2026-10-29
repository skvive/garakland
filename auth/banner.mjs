import { getSession, signOut } from './client.mjs';

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/"/g, '&quot;');
}

export async function mountAuthLink(linkId = 'authLink') {
  const el = document.getElementById(linkId);
  if (!el) return;
  try {
    const data = await getSession();
    if (data?.user?.email) {
      el.textContent = data.user.email.split('@')[0];
      el.href = '/login.html';
      el.title = `${data.user.email} — 계정 관리`;
      el.dataset.authed = '1';
    } else {
      el.textContent = '로그인';
      el.href = '/login.html';
    }
  } catch {
    el.textContent = '로그인';
    el.href = '/login.html';
  }
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-auth-signout]');
  if (!btn) return;
  e.preventDefault();
  await signOut();
  location.href = '/login.html';
});

mountAuthLink('authLink');
mountAuthLink('authLinkMarket');
