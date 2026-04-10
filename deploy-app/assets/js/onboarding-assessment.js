import { bindSignOut, bootstrapProtectedPage, getDraft, preloadDraftFromSupabase, saveDraft, ONBOARDING_ROUTES } from "./onboarding-flow.js";
import { routeTo } from "./state.js";

const statusEl = document.getElementById("assessment-status");
const limitationTags = [...document.querySelectorAll("[data-lim]")];
const screeningToggles = [...document.querySelectorAll("[data-fc]")];

const setup = await bootstrapProtectedPage(statusEl);
if (!setup.ready) {
  document.getElementById("next-assessment-btn").disabled = true;
} else {
  bindSignOut();
  const { user } = setup;
  const draft = await preloadDraftFromSupabase(user);

  document.getElementById("inp-doi").value = draft.date_of_injury || "";
  document.getElementById("inp-stage").value = draft.recovery_stage || "";
  document.getElementById("inp-notes").value = draft.additional_notes || "";
  document.getElementById("sl-daily").value = draft.pain_levels?.daily_overall ?? 3;
  document.getElementById("sl-squat").value = draft.pain_levels?.deep_squats ?? 5;
  document.getElementById("sl-stairs").value = draft.pain_levels?.stairs ?? 4;

  function syncPainValue(sliderId, valueId) {
    const slider = document.getElementById(sliderId);
    const value = document.getElementById(valueId);
    const render = () => {
      const v = Number(slider.value || 0);
      value.textContent = String(v);
      value.className = `pain-val${v >= 7 ? " hi" : v >= 4 ? " med" : ""}`;
    };
    render();
    slider.addEventListener("input", render);
  }

  syncPainValue("sl-daily", "v-daily");
  syncPainValue("sl-squat", "v-squat");
  syncPainValue("sl-stairs", "v-stairs");

  limitationTags.forEach((tag) => {
    tag.classList.toggle("sel", (draft.movement_limitations || []).includes(tag.dataset.lim));
    tag.addEventListener("click", () => tag.classList.toggle("sel"));
  });

  screeningToggles.forEach((button) => {
    const match = (draft.functional_screening || []).find((item) => item.key === button.dataset.fc || item.task === button.dataset.fc);
    if (match && match.success != null) {
      button.classList.toggle("on", String(match.success) === String(button.dataset.v === "yes"));
    }
    button.addEventListener("click", () => {
      document.querySelectorAll(`[data-fc="${button.dataset.fc}"]`).forEach((peer) => peer.classList.remove("on"));
      button.classList.add("on");
      const noteEl = document.getElementById(`fc-${button.dataset.fc}-note`);
      if (!noteEl) return;
      if (button.dataset.v === "no") {
        noteEl.style.display = "block";
        if (!noteEl.querySelector("input")) {
          const input = document.createElement("input");
          input.className = "discomfort-input";
          input.placeholder = "Describe the discomfort (optional)...";
          noteEl.appendChild(input);
        }
      } else {
        noteEl.style.display = "none";
      }
    });
  });

  document.getElementById("next-assessment-btn").addEventListener("click", () => {
    const functional_screening = [...new Set(screeningToggles.map((el) => el.dataset.fc))].map((key) => {
      const picked = document.querySelector(`[data-fc="${key}"].on`);
      const noteInput = document.querySelector(`#fc-${key}-note input`);
      return {
        key,
        task: key,
        success: picked ? picked.dataset.v === "yes" : null,
        discomfort_reported: noteInput ? noteInput.value.trim() : ""
      };
    });

    saveDraft({
      ...getDraft(),
      date_of_injury: document.getElementById("inp-doi").value || "",
      recovery_stage: document.getElementById("inp-stage").value || "",
      additional_notes: document.getElementById("inp-notes").value.trim(),
      pain_levels: {
        daily_overall: Number(document.getElementById("sl-daily").value || 0),
        deep_squats: Number(document.getElementById("sl-squat").value || 0),
        stairs: Number(document.getElementById("sl-stairs").value || 0)
      },
      functional_screening,
      movement_limitations: limitationTags.filter((tag) => tag.classList.contains("sel")).map((tag) => tag.dataset.lim)
    });

    routeTo(ONBOARDING_ROUTES.goals);
  });
}
