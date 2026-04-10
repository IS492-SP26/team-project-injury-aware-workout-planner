import { fetchAssessment, fetchProfile } from "./app-shell.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { routeTo, setStatus } from "./state.js";

const statusEl = document.getElementById("auth-status");
const tabs = [...document.querySelectorAll("[data-auth-mode]")];
const panels = [...document.querySelectorAll("[data-auth-panel]")];

function setMode(mode) {
  tabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.authMode === mode));
  panels.forEach((panel) => panel.classList.toggle("is-active", panel.dataset.authPanel === mode));
  setStatus(statusEl, "");
}

function describeError(error) {
  if (!error) return "Unknown authentication error.";
  const parts = [];
  if (error.message) parts.push(error.message);
  if (error.code) parts.push(`code: ${error.code}`);
  if (error.status) parts.push(`status: ${error.status}`);
  return parts.join(" | ");
}

tabs.forEach((tab) => tab.addEventListener("click", () => setMode(tab.dataset.authMode)));

if (!hasSupabaseConfig()) {
  setStatus(statusEl, "Add your Supabase URL and anon key in assets/js/config.js before using auth.", "danger");
} else {
  const supabase = requireSupabase();

  async function routeAuthenticatedUser() {
    const { data } = await supabase.auth.getSession();
    const user = data.session?.user;
    if (!user) return;

    const [profile, assessment] = await Promise.all([
      fetchProfile(user.id),
      fetchAssessment(user.id)
    ]);

    if (profile?.onboarding_completed && assessment) {
      routeTo("/workouts.html");
      return;
    }
    routeTo("/onboarding-basic.html");
  }

  function validEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
  }

  function validPassword(value) {
    return value.trim().length >= 8;
  }

  document.getElementById("sign-in-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("signin-email").value.trim();
    const password = document.getElementById("signin-password").value;

    if (!validEmail(email)) {
      setStatus(statusEl, "Enter a valid email address to sign in.", "danger");
      return;
    }
    if (!validPassword(password)) {
      setStatus(statusEl, "Password must be at least 8 characters.", "danger");
      return;
    }

    setStatus(statusEl, "Signing you in...");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      console.error("Supabase sign-in error", error);
      setStatus(statusEl, describeError(error), "danger");
      return;
    }

    setStatus(statusEl, "Signed in. Loading your workspace...", "success");
    await routeAuthenticatedUser();
  });

  document.getElementById("sign-up-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("signup-email").value.trim();
    const password = document.getElementById("signup-password").value;
    const confirm = document.getElementById("signup-confirm-password").value;

    if (!validEmail(email)) {
      setStatus(statusEl, "Enter a valid email address to create an account.", "danger");
      return;
    }
    if (!validPassword(password)) {
      setStatus(statusEl, "Password must be at least 8 characters.", "danger");
      return;
    }
    if (password !== confirm) {
      setStatus(statusEl, "Passwords do not match.", "danger");
      return;
    }

    setStatus(statusEl, "Creating your account...");
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) {
      console.error("Supabase sign-up error", error);
      setStatus(statusEl, describeError(error), "danger");
      return;
    }

    if (data.session) {
      setStatus(statusEl, "Account created. Continue to onboarding.", "success");
      routeTo("/onboarding-basic.html");
      return;
    }

    if (data.user) {
      setStatus(statusEl, "Account created. Check your email to confirm it before signing in.", "success");
      setMode("signin");
      document.getElementById("signin-email").value = email;
      return;
    }

    setStatus(statusEl, "Account created. Sign in to continue.", "success");
    setMode("signin");
    document.getElementById("signin-email").value = email;
  });

  document.getElementById("reset-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("reset-email").value.trim();
    if (!validEmail(email)) {
      setStatus(statusEl, "Enter a valid email address to receive a reset link.", "danger");
      return;
    }

    setStatus(statusEl, "Sending reset email...");
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/index.html`
    });
    if (error) {
      console.error("Supabase reset error", error);
      setStatus(statusEl, describeError(error), "danger");
      return;
    }

    setStatus(statusEl, "Password reset email sent. Check your inbox.", "success");
  });

  await routeAuthenticatedUser();
}
