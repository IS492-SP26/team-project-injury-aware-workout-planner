import { fetchAssessment, fetchProfile, requireUser, signOut } from "./app-shell.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { calculateReadiness } from "./readiness-score.js";
import { STORAGE_KEYS, readStorage, routeTo, saveStorage, setStatus } from "./state.js";

const statusEl = document.getElementById("readiness-status");
const scoreEl = document.getElementById("readiness-score");
const statusBadgeEl = document.getElementById("readiness-badge");
const recommendationEl = document.getElementById("readiness-recommendation");
const alertEl = document.getElementById("readiness-alert");
const alertTitleEl = document.getElementById("readiness-alert-title");
const alertCopyEl = document.getElementById("readiness-alert-copy");
const factorsEl = document.getElementById("readiness-factors");
const positivesEl = document.getElementById("readiness-positives");
const summaryEl = document.getElementById("readiness-summary");
const aiBoxEl = document.getElementById("readiness-ai-box");
const aiSummaryEl = document.getElementById("readiness-ai-summary");
const aiCautionEl = document.getElementById("readiness-ai-caution");
const aiNextEl = document.getElementById("readiness-ai-next");

async function fetchReadinessExplanation(payload) {
  const res = await fetch("/api/readiness/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Readiness explanation failed (${res.status})`);
  }
  return res.json();
}

if (!hasSupabaseConfig()) {
  setStatus(statusEl, "Add your Supabase configuration before using readiness scoring.", "danger");
  document.getElementById("continue-workouts-btn").disabled = true;
} else {
  const supabase = requireSupabase();
  const user = await requireUser("/index.html");
  if (!user) throw new Error("Authentication redirect failed.");

  document.getElementById("sign-out-btn").addEventListener("click", signOut);

  try {
    const [profile, assessment] = await Promise.all([
      fetchProfile(user.id),
      fetchAssessment(user.id)
    ]);

    if (!profile?.onboarding_completed || !assessment) {
      routeTo("/onboarding-basic.html");
    } else {
      const draft = readStorage(STORAGE_KEYS.onboardingDraft, {});
      const readiness = calculateReadiness({ profile, assessment, draft });
      saveStorage(STORAGE_KEYS.readinessSnapshot, readiness);

      scoreEl.textContent = String(readiness.score);
      statusBadgeEl.textContent = readiness.status;
      statusBadgeEl.dataset.tone = readiness.tone;
      recommendationEl.textContent = readiness.recommendation;
      if (readiness.highRiskConsultCase) {
        alertEl.className = "readiness-alert readiness-alert--critical";
        alertTitleEl.textContent = "High-risk recovery check";
        alertCopyEl.textContent =
          "We highly recommend you come back after consulting with a professional. If you still want to proceed, it is at your own risk.";
        alertEl.classList.remove("hidden");
        recommendationEl.classList.add("readiness-recommendation--critical");
      } else if (readiness.subAcuteWarningCase) {
        alertEl.className = "readiness-alert readiness-alert--soft";
        alertTitleEl.textContent = "Early recovery caution";
        alertCopyEl.textContent =
          "Your recovery is still in an early sub-acute window, so keep modifications conservative and pay close attention to pain or instability before progressing.";
        alertEl.classList.remove("hidden");
        recommendationEl.classList.remove("readiness-recommendation--critical");
      } else {
        alertEl.className = "readiness-alert hidden";
        alertEl.classList.add("hidden");
        recommendationEl.classList.remove("readiness-recommendation--critical");
      }
      summaryEl.textContent =
        `${readiness.summary.diagnosis || "Current injury"} | ${readiness.summary.recoveryStage || "Stage pending"} | ${readiness.summary.bodyPart || "Body part pending"}`;

      factorsEl.innerHTML = "";
      readiness.dominantFactors.forEach((factor) => {
        const item = document.createElement("div");
        item.className = "readiness-factor";
        item.innerHTML = `
          <div class="readiness-factor-head">
            <strong>${factor.label}</strong>
            <span>-${factor.penalty}</span>
          </div>
          <div class="readiness-factor-copy">${factor.detail}</div>
        `;
        factorsEl.appendChild(item);
      });

      positivesEl.innerHTML = "";
      (readiness.positiveSignals.length ? readiness.positiveSignals : ["The score is being driven mostly by current pain and recovery-stage factors."]).forEach((signal) => {
        const item = document.createElement("div");
        item.className = "readiness-positive";
        item.textContent = signal;
        positivesEl.appendChild(item);
      });

      try {
        const explanation = await fetchReadinessExplanation({
          readiness,
          profile: {
            age: profile.age,
            full_name: profile.full_name
          },
          assessment: {
            body_part: assessment.body_part,
            diagnosis: assessment.diagnosis,
            date_of_injury: assessment.date_of_injury,
            raw_payload: assessment.raw_payload
          }
        });
        aiSummaryEl.textContent = explanation.summary || "";
        aiCautionEl.textContent = explanation.caution || "";
        aiNextEl.textContent = explanation.next_step || "";
        aiBoxEl.classList.remove("hidden");
      } catch {
        aiBoxEl.classList.add("hidden");
      }

      document.getElementById("continue-workouts-btn").textContent = readiness.fitForSuggestions
        ? "Continue to Workout Modifications"
        : readiness.highRiskConsultCase
          ? "Proceed at Your Own Risk"
          : readiness.subAcuteWarningCase
            ? "Continue with Caution"
            : "Continue with Recovery-Focused Modifications";
      setStatus(
        statusEl,
        readiness.fitForSuggestions
          ? "Assessment saved. Readiness score calculated."
          : readiness.subAcuteWarningCase
            ? "Assessment saved. Stay conservative while symptoms settle."
            : "Assessment saved. Keep the next workout suggestions conservative.",
        readiness.fitForSuggestions ? "success" : readiness.subAcuteWarningCase ? "warning" : "danger"
      );
    }
  } catch (error) {
    setStatus(statusEl, error.message || "Failed to load readiness score.", "danger");
    document.getElementById("continue-workouts-btn").disabled = true;
  }
}

document.getElementById("continue-workouts-btn").addEventListener("click", () => routeTo("/workouts.html"));
