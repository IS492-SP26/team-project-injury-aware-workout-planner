import { bindSignOut, bootstrapProtectedPage, getDraft, missingBasicFields, preloadDraftFromSupabase, saveDraft, ONBOARDING_ROUTES } from "./onboarding-flow.js";
import { routeTo, setStatus } from "./state.js";

const statusEl = document.getElementById("basic-status");
const setup = await bootstrapProtectedPage(statusEl);
if (!setup.ready) {
  document.getElementById("next-basic-btn").disabled = true;
} else {
  bindSignOut();
  const { user } = setup;
  const draft = await preloadDraftFromSupabase(user, { force: true });

  document.getElementById("full-name").value = draft.name || "";
  document.getElementById("age").value = draft.age || "";
  document.getElementById("gender").value = draft.gender || "";
  document.getElementById("height-unit").value = draft.height_unit || "cm";
  document.getElementById("height-value").value = draft.height_value || "";

  document.getElementById("next-basic-btn").addEventListener("click", () => {
    const next = saveDraft({
      ...getDraft(),
      name: document.getElementById("full-name").value.trim(),
      age: document.getElementById("age").value,
      gender: document.getElementById("gender").value,
      height_unit: document.getElementById("height-unit").value,
      height_value: document.getElementById("height-value").value
    });

    const missing = missingBasicFields(next);

    if (missing.length) {
      setStatus(statusEl, `Missing required field${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}.`, "danger");
      return;
    }

    routeTo(ONBOARDING_ROUTES.injury);
  });
}
