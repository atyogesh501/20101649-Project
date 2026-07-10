import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.9.0/firebase-app.js';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from 'https://www.gstatic.com/firebasejs/12.9.0/firebase-auth.js';

const firebaseConfig = {
  apiKey: "AIzaSyDUX9ua68ylmjP4wLtiDMCIcoJ8q4lYHgE",
  authDomain: "project-72755.firebaseapp.com",
  projectId: "project-72755",
  storageBucket: "project-72755.firebasestorage.app",
  messagingSenderId: "88529734374",
  appId: "1:88529734374:web:b411611abb8480f78e0927",
  measurementId: "G-Y4JKBF2WMQ"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

function saveUserToCookie(token) {
  document.cookie = `token=${token}; path=/; max-age=3600`;
}

function clearUserCookie() {
  document.cookie = 'token=; path=/; max-age=0';
}

async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, provider);
    const token = await result.user.getIdToken();
    saveUserToCookie(token);
    try { localStorage.removeItem('connectAiChatHistory'); } catch (e) {}
    return { success: true, user: result.user };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function logOut() {
  try {
    await signOut(auth);
    clearUserCookie();
    try { localStorage.removeItem('connectAiChatHistory'); } catch (e) {}
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

onAuthStateChanged(auth, async (user) => {
  if (user) {
    const token = await user.getIdToken();
    saveUserToCookie(token);
  } else {
    clearUserCookie();
  }
});

window.firebaseAuth = {
  signInWithGoogle,
  logOut,
  auth,
};

document.addEventListener('DOMContentLoaded', () => {
  const googleBtn = document.getElementById('google-signin-btn');
  const logoutBtn = document.getElementById('logout-btn');

  if (googleBtn) {
    googleBtn.addEventListener('click', async () => {
      const errorDiv = document.getElementById('login-error');
      if (errorDiv) errorDiv.textContent = '';
      googleBtn.disabled = true;
      const result = await signInWithGoogle();
      if (result.success) {
        window.location.reload();
      } else {
        googleBtn.disabled = false;
        if (errorDiv) errorDiv.textContent = result.error;
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      const result = await logOut();
      if (result.success) {
        window.location.reload();
      }
    });
  }
});
