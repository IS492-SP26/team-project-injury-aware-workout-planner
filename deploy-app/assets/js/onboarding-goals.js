import { bindSignOut, bootstrapProtectedPage, finalizeOnboarding, getDraft, preloadDraftFromSupabase, saveDraft } from "./onboarding-flow.js";
import { routeTo, setStatus } from "./state.js";

const statusEl = document.getElementById("goals-status");
const goalCards = [...document.querySelectorAll("[data-goal]")];
const levelCards = [...document.querySelectorAll("[data-lv]")];
const activityCards = [...document.querySelectorAll("[data-al]")];

const setup = await bootstrapProtectedPage(statusEl);
if (!setup.ready) {
  document.getElementById("finish-onboarding-btn").disabled = true;
} else {
  bindSignOut();
  const { supabase, user } = setup;
  const draft = await preloadDraftFromSupabase(user);

  levelCards.forEach((card) => {
    card.classList.toggle("sel", card.dataset.lv === draft.levelLabel);
    card.addEventListener("click", () => {
      levelCards.forEach((peer) => peer.classList.remove("sel"));
      card.classList.add("sel");
    });
  });

  activityCards.forEach((card) => {
    card.classList.toggle("sel", card.dataset.al === draft.activityLevelLabel);
    card.addEventListener("click", () => {
      activityCards.forEach((peer) => peer.classList.remove("sel"));
      card.classList.add("sel");
    });
  });

  goalCards.forEach((card) => {
    card.classList.toggle("sel", (draft.goals || []).includes(card.dataset.goal));
    card.addEventListener("click", () => card.classList.toggle("sel"));
  });

  document.getElementById("finish-onboarding-btn").addEventListener("click", async () => {
    const selectedLevel = levelCards.find((card) => card.classList.contains("sel"))?.dataset.lv || "";
    const selectedActivity = activityCards.find((card) => card.classList.contains("sel"))?.dataset.al || "";
    const selectedGoals = goalCards.filter((card) => card.classList.contains("sel")).map((card) => card.dataset.goal);

    saveDraft({
      ...getDraft(),
      levelLabel: selectedLevel,
      activityLevelLabel: selectedActivity,
      goals: selectedGoals,
      goalLabels: selectedGoals
    });

    try {
      await finalizeOnboarding({ supabase, user, statusEl });
      setStatus(statusEl, "Saved. Opening workout import...", "success");
      routeTo("/workouts.html");
    } catch (error) {
      setStatus(statusEl, error.message || "Failed to save onboarding.", "danger");
    }
  });
}
