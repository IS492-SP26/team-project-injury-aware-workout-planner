import { fetchAssessment, fetchProfile, requireUser, signOut } from "./app-shell.js";
import { submitSurveyToBackend } from "./api.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { STORAGE_KEYS, routeTo, saveStorage, setStatus } from "./state.js";

const fields = {
  fullName: document.getElementById("full-name"),
  age: document.getElementById("age"),
  gender: document.getElementById("gender"),
  heightUnit: document.getElementById("height-unit"),
  heightValue: document.getElementById("height-value"),
  bodyPart: document.getElementById("body-part"),
  diagnosis: document.getElementById("diagnosis"),
  dateOfInjury: document.getElementById("date-of-injury"),
  trainingExperience: document.getElementById("training-experience"),
  activityLevel: document.getElementById("activity-level"),
  painDaily: document.getElementById("pain-daily"),
  painSquat: document.getElementById("pain-squat"),
  painStairs: document.getElementById("pain-stairs")
};

const statusEl = document.getElementById("onboarding-status");
const goalCards = [...document.querySelectorAll("[data-goal]")];
const limitationCards = [...document.querySelectorAll("[data-limitation]")];
const screeningToggles = [...document.querySelectorAll("[data-screening]")];

function toggleSelection(el) {
  el.classList.toggle("is-selected");
}

goalCards.forEach((card) => card.addEventListener("click", () => toggleSelection(card)));
limitationCards.forEach((card) => card.addEventListener("click", () => toggleSelection(card)));
screeningToggles.forEach((card) => card.addEventListener("click", () => {
  const group = card.dataset.screening;
  document.querySelectorAll(`[data-screening="${group}"]`).forEach((peer) => peer.classList.remove("is-selected"));
  card.classList.add("is-selected");
}));

if (!hasSupabaseConfig()) {
  setStatus(statusEl, "Add your Supabase URL and anon key in assets/js/config.js before using onboarding.", "danger");
  document.getElementById("save-onboarding-btn").disabled = true;
} else {
  const supabase = requireSupabase();
  const user = await requireUser("/index.html");
  if (!user) throw new Error("Authentication redirect failed.");

  document.getElementById("sign-out-btn").addEventListener("click", signOut);

function selectedValues(selector, attr) {
  return [...document.querySelectorAll(selector)]
    .filter((el) => el.classList.contains("is-selected"))
    .map((el) => el.dataset[attr]);
}

function selectedScreening() {
  return [...new Set(screeningToggles.map((el) => el.dataset.screening))].map((key) => {
    const picked = document.querySelector(`[data-screening="${key}"].is-selected`);
    return {
      task: key,
      success: picked ? picked.dataset.value === "yes" : null
    };
  });
}

function buildRawPayload() {
  const goals = selectedValues("[data-goal]", "goal");
  const movementLimitations = selectedValues("[data-limitation]", "limitation");
  return {
    name: fields.fullName.value.trim(),
    age: Number(fields.age.value || 0) || null,
    gender: fields.gender.value,
    height_unit: fields.heightUnit.value,
    height_value: Number(fields.heightValue.value || 0) || null,
    zone: fields.bodyPart.value,
    injuryLabel: fields.diagnosis.value.trim(),
    date_of_injury: fields.dateOfInjury.value || null,
    levelLabel: fields.trainingExperience.value,
    activityLevelLabel: fields.activityLevel.value,
    goals,
    goalLabels: goals,
    pain_levels: {
      daily_overall: Number(fields.painDaily.value || 0),
      deep_squats: Number(fields.painSquat.value || 0),
      stairs: Number(fields.painStairs.value || 0)
    },
    functional_screening: selectedScreening(),
    movement_limitations: movementLimitations
  };
}

function missingRequiredFields(raw) {
  const missing = [];
  if (!raw.name) missing.push("full name");
  if (!raw.age || Number.isNaN(Number(raw.age))) missing.push("age");
  if (!raw.gender) missing.push("gender");
  if (!raw.zone) missing.push("body part");
  if (!raw.injuryLabel) missing.push("diagnosis");
  return missing;
}

function profilePayload(raw) {
  return {
    id: user.id,
    email: user.email,
    full_name: raw.name,
    age: raw.age,
    gender: raw.gender,
    height_unit: raw.height_unit,
    height_value: raw.height_value,
    onboarding_completed: true
  };
}

function assessmentPayload(raw, backendSessionId) {
  return {
    user_id: user.id,
    body_part: raw.zone,
    diagnosis: raw.injuryLabel,
    date_of_injury: raw.date_of_injury,
    training_experience: raw.levelLabel,
    activity_level: raw.activityLevelLabel,
    goals: raw.goals,
    pain_daily: raw.pain_levels.daily_overall,
    pain_squat: raw.pain_levels.deep_squats,
    pain_stairs: raw.pain_levels.stairs,
    functional_screening: raw.functional_screening,
    movement_limitations: raw.movement_limitations,
    raw_payload: raw,
    backend_session_id: backendSessionId
  };
}

async function preload() {
  const [profile, assessment] = await Promise.all([
    fetchProfile(user.id),
    fetchAssessment(user.id)
  ]);

  if (profile) {
    fields.fullName.value = profile.full_name || "";
    fields.age.value = profile.age || "";
    fields.gender.value = profile.gender || "";
    fields.heightUnit.value = profile.height_unit || "cm";
    fields.heightValue.value = profile.height_value || "";
  }

  if (assessment) {
    fields.bodyPart.value = assessment.body_part || "";
    fields.diagnosis.value = assessment.diagnosis || "";
    fields.dateOfInjury.value = assessment.date_of_injury || "";
    fields.trainingExperience.value = assessment.training_experience || "";
    fields.activityLevel.value = assessment.activity_level || "";
    fields.painDaily.value = assessment.pain_daily ?? 3;
    fields.painSquat.value = assessment.pain_squat ?? 4;
    fields.painStairs.value = assessment.pain_stairs ?? 4;

    const goals = assessment.goals || [];
    goalCards.forEach((card) => {
      card.classList.toggle("is-selected", goals.includes(card.dataset.goal));
    });

    const limitations = assessment.movement_limitations || [];
    limitationCards.forEach((card) => {
      card.classList.toggle("is-selected", limitations.includes(card.dataset.limitation));
    });

    const screening = assessment.functional_screening || [];
    screening.forEach((item) => {
      if (item.success == null) return;
      const selector = `[data-screening="${item.task}"][data-value="${item.success ? "yes" : "no"}"]`;
      const match = document.querySelector(selector);
      if (match) match.classList.add("is-selected");
    });
  }
}

document.getElementById("save-onboarding-btn").addEventListener("click", async () => {
  const raw = buildRawPayload();
  const missing = missingRequiredFields(raw);
  if (missing.length) {
    setStatus(statusEl, `Missing required field${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}.`, "danger");
    return;
  }

  try {
    setStatus(statusEl, "Saving profile and syncing assessment...");
    const surveyResponse = await submitSurveyToBackend(raw);
    const backendSessionId = surveyResponse.session_id;

    const { error: profileError } = await supabase.from("users").upsert(profilePayload(raw));
    if (profileError) throw profileError;

    const { error: assessmentError } = await supabase.from("injury_assessments").upsert(assessmentPayload(raw, backendSessionId));
    if (assessmentError) throw assessmentError;

    saveStorage(STORAGE_KEYS.backendSessionId, backendSessionId);
    saveStorage(STORAGE_KEYS.onboardingDraft, raw);
    setStatus(statusEl, "Saved. Opening workout import...", "success");
    routeTo("/workouts.html");
  } catch (error) {
    setStatus(statusEl, error.message || "Failed to save onboarding.", "danger");
  }
});

  await preload();
}
