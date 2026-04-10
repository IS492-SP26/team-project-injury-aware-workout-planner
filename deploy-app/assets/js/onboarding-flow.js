import { fetchAssessment, fetchProfile, requireUser, signOut } from "./app-shell.js";
import { submitSurveyToBackend } from "./api.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { STORAGE_KEYS, readStorage, routeTo, saveStorage, setStatus } from "./state.js";

export const ONBOARDING_ROUTES = {
  basic: "/onboarding-basic.html",
  injury: "/onboarding-injury.html",
  assessment: "/onboarding-assessment.html",
  goals: "/onboarding-goals.html"
};

const DEFAULT_DRAFT = {
  name: "",
  age: "",
  gender: "",
  height_unit: "cm",
  height_value: "",
  zone: "",
  injuryLabel: "",
  date_of_injury: "",
  recovery_stage: "",
  additional_notes: "",
  levelLabel: "",
  activityLevelLabel: "",
  goals: [],
  goalLabels: [],
  pain_levels: {
    daily_overall: 3,
    deep_squats: 5,
    stairs: 4
  },
  functional_screening: [],
  movement_limitations: []
};

export function getDraft() {
  return {
    ...DEFAULT_DRAFT,
    ...readStorage(STORAGE_KEYS.onboardingDraft, {})
  };
}

export function saveDraft(patch) {
  const next = { ...getDraft(), ...patch };
  saveStorage(STORAGE_KEYS.onboardingDraft, next);
  return next;
}

export async function bootstrapProtectedPage(statusEl) {
  if (!hasSupabaseConfig()) {
    if (statusEl) setStatus(statusEl, "Add your Supabase URL and anon key in assets/js/config.js before using onboarding.", "danger");
    return { ready: false };
  }

  const supabase = requireSupabase();
  const user = await requireUser("/index.html");
  if (!user) return { ready: false };

  return { ready: true, supabase, user };
}

export async function preloadDraftFromSupabase(user) {
  const [profile, assessment] = await Promise.all([
    fetchProfile(user.id),
    fetchAssessment(user.id)
  ]);

  const merged = {
    ...getDraft(),
    name: profile?.full_name || getDraft().name,
    age: profile?.age ?? getDraft().age,
    gender: profile?.gender || getDraft().gender,
    height_unit: profile?.height_unit || getDraft().height_unit,
    height_value: profile?.height_value ?? getDraft().height_value,
    zone: assessment?.body_part || getDraft().zone,
    injuryLabel: assessment?.diagnosis || getDraft().injuryLabel,
    date_of_injury: assessment?.date_of_injury || getDraft().date_of_injury,
    recovery_stage: assessment?.raw_payload?.recovery_stage || getDraft().recovery_stage,
    additional_notes: assessment?.raw_payload?.additional_notes || getDraft().additional_notes,
    levelLabel: assessment?.training_experience || getDraft().levelLabel,
    activityLevelLabel: assessment?.activity_level || getDraft().activityLevelLabel,
    goals: assessment?.goals || getDraft().goals,
    goalLabels: assessment?.goals || getDraft().goalLabels,
    pain_levels: {
      daily_overall: assessment?.pain_daily ?? getDraft().pain_levels.daily_overall,
      deep_squats: assessment?.pain_squat ?? getDraft().pain_levels.deep_squats,
      stairs: assessment?.pain_stairs ?? getDraft().pain_levels.stairs
    },
    functional_screening: assessment?.functional_screening || getDraft().functional_screening,
    movement_limitations: assessment?.movement_limitations || getDraft().movement_limitations
  };

  saveStorage(STORAGE_KEYS.onboardingDraft, merged);
  return merged;
}

export function bindSignOut() {
  const btn = document.getElementById("sign-out-btn");
  if (btn) btn.addEventListener("click", signOut);
}

export function missingBasicFields(raw) {
  const missing = [];
  if (!raw.name) missing.push("full name");
  if (!raw.age || Number.isNaN(Number(raw.age))) missing.push("age");
  if (!raw.gender) missing.push("gender");
  return missing;
}

export function missingInjuryFields(raw) {
  const missing = [];
  if (!raw.zone) missing.push("body part");
  if (!raw.injuryLabel) missing.push("diagnosis");
  return missing;
}

export function profilePayload(user, raw) {
  return {
    id: user.id,
    email: user.email,
    full_name: raw.name,
    age: Number(raw.age || 0) || null,
    gender: raw.gender,
    height_unit: raw.height_unit,
    height_value: Number(raw.height_value || 0) || null,
    onboarding_completed: true
  };
}

export function assessmentPayload(user, raw, backendSessionId) {
  return {
    user_id: user.id,
    body_part: raw.zone,
    diagnosis: raw.injuryLabel,
    date_of_injury: raw.date_of_injury || null,
    training_experience: raw.levelLabel || null,
    activity_level: raw.activityLevelLabel || null,
    goals: raw.goals || [],
    pain_daily: Number(raw.pain_levels?.daily_overall || 0) || null,
    pain_squat: Number(raw.pain_levels?.deep_squats || 0) || null,
    pain_stairs: Number(raw.pain_levels?.stairs || 0) || null,
    functional_screening: raw.functional_screening || [],
    movement_limitations: raw.movement_limitations || [],
    raw_payload: raw,
    backend_session_id: backendSessionId
  };
}

export async function finalizeOnboarding({ supabase, user, statusEl }) {
  const raw = getDraft();
  const basicMissing = missingBasicFields(raw);
  if (basicMissing.length) {
    setStatus(statusEl, `Missing required field${basicMissing.length > 1 ? "s" : ""}: ${basicMissing.join(", ")}.`, "danger");
    routeTo(ONBOARDING_ROUTES.basic);
    return;
  }

  const injuryMissing = missingInjuryFields(raw);
  if (injuryMissing.length) {
    setStatus(statusEl, `Missing required field${injuryMissing.length > 1 ? "s" : ""}: ${injuryMissing.join(", ")}.`, "danger");
    routeTo(ONBOARDING_ROUTES.injury);
    return;
  }

  setStatus(statusEl, "Saving profile and syncing assessment...");
  const surveyResponse = await submitSurveyToBackend(raw);
  const backendSessionId = surveyResponse.session_id;

  const { error: profileError } = await supabase.from("users").upsert(profilePayload(user, raw));
  if (profileError) throw profileError;

  const { error: assessmentError } = await supabase.from("injury_assessments").upsert(
    assessmentPayload(user, raw, backendSessionId)
  );
  if (assessmentError) throw assessmentError;

  saveStorage(STORAGE_KEYS.backendSessionId, backendSessionId);
  saveStorage(STORAGE_KEYS.onboardingDraft, raw);
}
