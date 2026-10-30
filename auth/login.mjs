import { getAuthClient, getSession, signOut, signInWithGoogle } from './client.mjs';

const form = document.getElementById('authForm');
const logged = document.getElementById('loggedPanel');
const msg = document.getElementById('authMsg');
const modeSignUpWrap = document.getElementById('modeSignUpWrap');
const modeSignInWrap = document.getElementById('modeSignInWrap');
const title = document.getElementById('authTitle');
const submitBtn = document.getElementById('authSubmit');
const userEmail = document.getElementById('userEmail');

let signUp = true;

function setMsg(text, kind = '') {
  msg.textContent = text;
  msg.className = 'auth-msg' + (kind ? ` ${kind}` : '');
}

function setMode(up) {
  signUp = up;
  title.textContent = up ? '가락한상 계정 만들기' : '로그인';
  submitBtn.textContent = up ? '이메일로 가입' : '로그인';
  modeSignUpWrap.hidden = up;
  modeSignInWrap.hidden = !up;
}

document.getElementById('modeSignUpBtn')?.addEventListener('click', () => setMode(true));
document.getElementById('modeSignInBtn')?.addEventListener('click', () => setMode(false));

document.getElementById('googleBtn')?.addEventListener('click', async () => {
  setMsg('Google 계정 선택 화면으로 이동합니다…');
  try {
    const result = await signInWithGoogle(`${window.location.origin}/login.html`);
    if (result?.error) {
      setMsg(result.error.message || 'Google 로그인에 실패했습니다.', 'error');
    }
  } catch (err) {
    setMsg(err?.message || 'Google 로그인에 실패했습니다.', 'error');
  }
});

async function showLogged(user) {
  form.hidden = true;
  logged.hidden = false;
  userEmail.textContent = user.email;
}

async function refresh() {
  const data = await getSession();
  if (data?.user) {
    await showLogged(data.user);
  }
}

document.getElementById('signOutBtn')?.addEventListener('click', async () => {
  await signOut();
  form.hidden = false;
  logged.hidden = true;
  setMsg('로그아웃했습니다.', 'ok');
});

form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  setMsg('처리 중…');
  const email = form.email.value.trim();
  const password = form.password.value;
  const auth = await getAuthClient();
  const result = signUp
    ? await auth.signUp.email({ name: email.split('@')[0] || '탐험가', email, password })
    : await auth.signIn.email({ email, password });

  if (result.error) {
    setMsg(result.error.message || '인증에 실패했습니다.', 'error');
    return;
  }

  const session = await getSession();
  if (session?.user) {
    setMsg('환영합니다!', 'ok');
    await showLogged(session.user);
    return;
  }
  setMsg(signUp ? '가입 완료. 이메일 확인이 필요할 수 있습니다.' : '로그인되었습니다.', 'ok');
});

setMode(true);
if (new URLSearchParams(location.search).get('error')) {
  setMsg('Google 로그인이 취소되었거나 실패했습니다. 다시 시도해 주세요.', 'error');
}
refresh().catch(() => setMsg(''));
