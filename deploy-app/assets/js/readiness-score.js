function normalizeText(value) {
  return String(value || "").trim().toLowerCase();
}

function parseDateToAgeDays(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  const diffMs = Date.now() - date.getTime();
  return Math.max(0, Math.round(diffMs / 86400000));
}

function diagnosisPenalty(diagnosis) {
  const map = {
    "acl reconstruction": 18,
    "meniscal repair": 14,
    "patellofemoral pain": 8,
    "knee osteoarthritis": 12,
    "rotator cuff": 12,
    "impingement": 8,
    "labral tear": 14,
    "instability": 16
  };
  const key = normalizeText(diagnosis);
  if (!key) return 10;
  return map[key] ?? 10;
}

function stagePenalty(stage) {
  const key = normalizeText(stage);
  if (!key) return 8;
  if (key.includes("acute")) return 20;
  if (key.includes("sub-acute")) return 14;
  if (key.includes("mid-stage")) return 9;
  if (key.includes("late-stage")) return 5;
  if (key.includes("return")) return 0;
  return 8;
}

function buildFactor(label, penalty, detail) {
  return { label, penalty, detail };
}

export function calculateReadiness({ profile, assessment, draft }) {
  const raw = draft || assessment?.raw_payload || {};
  const pain = {
    daily: Number(assessment?.pain_daily ?? raw?.pain_levels?.daily_overall ?? 0) || 0,
    squat: Number(assessment?.pain_squat ?? raw?.pain_levels?.deep_squats ?? 0) || 0,
    stairs: Number(assessment?.pain_stairs ?? raw?.pain_levels?.stairs ?? 0) || 0
  };
  const screening = Array.isArray(assessment?.functional_screening)
    ? assessment.functional_screening
    : Array.isArray(raw.functional_screening)
      ? raw.functional_screening
      : [];
  const movementLimitations = Array.isArray(assessment?.movement_limitations)
    ? assessment.movement_limitations
    : Array.isArray(raw.movement_limitations)
      ? raw.movement_limitations
      : [];

  const factors = [];
  factors.push(
    buildFactor(
      "Injury profile",
      diagnosisPenalty(assessment?.diagnosis || raw.injuryLabel),
      assessment?.diagnosis || raw.injuryLabel || "Undiagnosed injury"
    )
  );
  factors.push(
    buildFactor(
      "Recovery stage",
      stagePenalty(raw.recovery_stage),
      raw.recovery_stage || "Stage not specified"
    )
  );

  const averagePain = (pain.daily + pain.squat + pain.stairs) / 3;
  const painPenalty = Math.round(averagePain * 3.5) + (Math.max(pain.daily, pain.squat, pain.stairs) >= 8 ? 8 : 0);
  factors.push(
    buildFactor(
      "Pain load",
      painPenalty,
      `Daily ${pain.daily}/10, squat ${pain.squat}/10, stairs ${pain.stairs}/10`
    )
  );

  const failedScreens = screening.filter((item) => item && item.success === false);
  const unknownScreens = screening.filter((item) => item && item.success == null);
  const screeningPenalty = failedScreens.length * 8 + unknownScreens.length * 3;
  factors.push(
    buildFactor(
      "Functional screening",
      screeningPenalty,
      failedScreens.length
        ? `${failedScreens.length} task(s) not completed comfortably`
        : unknownScreens.length
          ? `${unknownScreens.length} task(s) unanswered`
          : "All screening tasks passed"
    )
  );

  const limitationPenalty = Math.min(movementLimitations.length * 3, 15);
  factors.push(
    buildFactor(
      "Movement limitations",
      limitationPenalty,
      movementLimitations.length
        ? movementLimitations.join(", ")
        : "No extra limitations reported"
    )
  );

  const injuryAgeDays = parseDateToAgeDays(assessment?.date_of_injury || raw.date_of_injury);
  if (injuryAgeDays != null && injuryAgeDays < 42) {
    factors.push(
      buildFactor(
        "Recent injury timing",
        10,
        `${injuryAgeDays} day(s) since injury date`
      )
    );
  }

  const notes = normalizeText(raw.additional_notes);
  if (notes.includes("surgery") || notes.includes("reconstruction") || notes.includes("post-op")) {
    factors.push(buildFactor("Surgical recovery", 6, "Additional notes mention surgery or post-op recovery"));
  }

  let score = 100 - factors.reduce((sum, factor) => sum + factor.penalty, 0);
  score = Math.max(0, Math.min(100, score));

  let status = "Ready for modified suggestions";
  let tone = "success";
  let fitForSuggestions = true;
  if (score < 60) {
    status = "Recovery-first focus";
    tone = "danger";
    fitForSuggestions = false;
  } else if (score < 80) {
    status = "Proceed with caution";
    tone = "warning";
  }

  const dominantFactors = factors
    .filter((factor) => factor.penalty > 0)
    .sort((a, b) => b.penalty - a.penalty)
    .slice(0, 3);

  const positiveSignals = [];
  if (averagePain <= 3) positiveSignals.push("Pain levels are in a manageable range");
  if (!failedScreens.length) positiveSignals.push("Functional screening does not show clear task failure");
  if (!movementLimitations.length) positiveSignals.push("No additional movement limitations were flagged");

  const recommendation =
    fitForSuggestions
      ? "You can move forward with injury-aware workout modifications, while still respecting pain signals and range limits."
      : "It is safer to prioritize recovery-friendly guidance first and keep workout modifications conservative until symptoms settle.";

  return {
    score,
    status,
    tone,
    fitForSuggestions,
    recommendation,
    dominantFactors,
    positiveSignals,
    factors,
    summary: {
      bodyPart: assessment?.body_part || raw.zone || "",
      diagnosis: assessment?.diagnosis || raw.injuryLabel || "",
      recoveryStage: raw.recovery_stage || "",
      age: profile?.age ?? raw.age ?? null
    }
  };
}
