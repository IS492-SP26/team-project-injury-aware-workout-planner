import { bindSignOut, bootstrapProtectedPage, getDraft, missingInjuryFields, preloadDraftFromSupabase, saveDraft, ONBOARDING_ROUTES } from "./onboarding-flow.js";
import { routeTo, setStatus } from "./state.js";

const statusEl = document.getElementById("injury-status");
const nextBtn = document.getElementById("next-injury-btn");
const hintEl = document.getElementById("p2hint");
const bodyStage = document.getElementById("body-stage");
const bodyCenter = document.getElementById("bodyCenter");
const panelKnee = document.getElementById("panel-knee");
const panelShoulder = document.getElementById("panel-shoulder");

const injuryLabels = {
  acl: "ACL Reconstruction",
  meniscal: "Meniscal Repair",
  pfp: "Patellofemoral Pain",
  oa: "Knee Osteoarthritis",
  rotator: "Rotator Cuff",
  impingement: "Shoulder Impingement",
  labrum: "Labral Tear",
  instability: "Shoulder Instability"
};

function placeInjuryPanels() {
  if (!bodyStage || !bodyCenter || !panelKnee || !panelShoulder) return;

  const gap = window.innerWidth < 980 ? 6 : 10;
  const centerLeft = bodyCenter.offsetLeft;
  const centerRight = centerLeft + bodyCenter.offsetWidth;
  const stageWidth = bodyStage.clientWidth;
  const leftWidth = panelKnee.offsetWidth;
  const rightWidth = panelShoulder.offsetWidth;

  let leftX = centerLeft - leftWidth - gap;
  let rightX = centerRight + gap;

  leftX = Math.max(0, leftX);
  rightX = Math.min(stageWidth - rightWidth, rightX);

  panelKnee.style.left = `${leftX}px`;
  panelShoulder.style.left = `${rightX}px`;
}

function paintZone(zone) {
  const kOpacity = zone === "knee" ? "0.15" : "0";
  const sOpacity = zone === "shoulder" ? "0.15" : "0";
  const kStroke = zone === "knee" ? "0.6" : "0";
  const sStroke = zone === "shoulder" ? "0.6" : "0";

  document.getElementById("hl-knee-l").setAttribute("fill", `rgba(245,91,91,${kOpacity})`);
  document.getElementById("hl-knee-r").setAttribute("fill", `rgba(245,91,91,${kOpacity})`);
  document.getElementById("hl-knee-l").setAttribute("stroke", `rgba(245,91,91,${kStroke})`);
  document.getElementById("hl-knee-r").setAttribute("stroke", `rgba(245,91,91,${kStroke})`);
  document.getElementById("hl-sh-l").setAttribute("fill", `rgba(91,142,245,${sOpacity})`);
  document.getElementById("hl-sh-r").setAttribute("fill", `rgba(91,142,245,${sOpacity})`);
  document.getElementById("hl-sh-l").setAttribute("stroke", `rgba(91,142,245,${sStroke})`);
  document.getElementById("hl-sh-r").setAttribute("stroke", `rgba(91,142,245,${sStroke})`);
}

function resetInjurySelection() {
  document.querySelectorAll(".inj-card,.unknown-opt").forEach((node) => node.classList.remove("sel"));
  nextBtn.disabled = true;
}

function showNeutralState() {
  document.querySelectorAll(".hs").forEach((hotspot) => hotspot.classList.remove("lit"));
  paintZone("");
  panelKnee.classList.remove("visible");
  panelShoulder.classList.remove("visible");
  resetInjurySelection();
  hintEl.textContent = "Tap a body region";
}

function showZone(zone) {
  document.querySelectorAll(".hs").forEach((hotspot) => {
    hotspot.classList.toggle("lit", hotspot.dataset.zone === zone);
  });
  paintZone(zone);
  panelKnee.classList.toggle("visible", zone === "knee");
  panelShoulder.classList.toggle("visible", zone === "shoulder");
  resetInjurySelection();
  saveDraft({ ...getDraft(), zone, injuryLabel: "" });
  hintEl.textContent = `Now pick your ${zone} injury`;
}

const setup = await bootstrapProtectedPage(statusEl);
if (!setup.ready) {
  nextBtn.disabled = true;
} else {
  bindSignOut();
  const { user } = setup;
  await preloadDraftFromSupabase(user);

  window.addEventListener("resize", placeInjuryPanels);
  requestAnimationFrame(placeInjuryPanels);
  showNeutralState();
  saveDraft({ ...getDraft(), zone: "", injuryLabel: "" });

  document.querySelectorAll(".hs").forEach((hotspot) => {
    hotspot.addEventListener("click", () => showZone(hotspot.dataset.zone));
  });

  document.querySelectorAll(".inj-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".inj-card,.unknown-opt").forEach((node) => node.classList.remove("sel"));
      card.classList.add("sel");
      const next = saveDraft({
        ...getDraft(),
        zone: card.dataset.zone,
        injuryLabel: injuryLabels[card.dataset.inj] || ""
      });
      nextBtn.disabled = false;
      hintEl.textContent = `${next.injuryLabel} selected`;
      paintZone(card.dataset.zone);
    });
  });

  document.querySelectorAll(".unknown-opt").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".inj-card,.unknown-opt").forEach((node) => node.classList.remove("sel"));
      card.classList.add("sel");
      const next = saveDraft({
        ...getDraft(),
        zone: card.dataset.zone,
        injuryLabel: `Undiagnosed ${card.dataset.zone} injury`
      });
      nextBtn.disabled = false;
      hintEl.textContent = `${next.injuryLabel} selected`;
      paintZone(card.dataset.zone);
    });
  });

  nextBtn.addEventListener("click", () => {
    const next = getDraft();
    const missing = missingInjuryFields(next);
    if (missing.length) {
      setStatus(statusEl, `Missing required field${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}.`, "danger");
      return;
    }
    routeTo(ONBOARDING_ROUTES.assessment);
  });
}
