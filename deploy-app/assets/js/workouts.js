import {
  buildAdaptFitPlaybackDocument,
  buildReuseVideoInformationForApi
} from "./adaptfit-playback-format.js";
import { fetchAssessment, fetchProfile, requireUser, signOut } from "./app-shell.js";
import { analyzeWorkoutWithBackend } from "./api.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { STORAGE_KEYS, formatTimestampRange, readStorage, routeTo, saveStorage, setStatus } from "./state.js";
import { extractYouTubeVideoId } from "./youtube-player.js";

const statusEl = document.getElementById("analysis-status");
const sourceTabs = [...document.querySelectorAll("[data-source-tab]")];
const sourcePanels = {
  youtube: document.getElementById("youtube-panel"),
  text: document.getElementById("text-panel")
};

let source = "youtube";
let latestProfile = null;
let latestAssessment = null;

function switchSource(next) {
  source = next;
  sourceTabs.forEach((tab) => tab.classList.toggle("is-selected", tab.dataset.sourceTab === next));
  Object.entries(sourcePanels).forEach(([key, panel]) => panel.classList.toggle("hidden", key !== next));
}

sourceTabs.forEach((tab) => {
  tab.addEventListener("click", () => switchSource(tab.dataset.sourceTab));
});

if (!hasSupabaseConfig()) {
  setStatus(statusEl, "Add your Supabase URL and anon key in assets/js/config.js before analyzing workouts.", "danger");
  document.getElementById("analyze-btn").disabled = true;
} else {
  const supabase = requireSupabase();
  const user = await requireUser("/index.html");
  if (!user) throw new Error("Authentication redirect failed.");

  document.getElementById("sign-out-btn").addEventListener("click", signOut);

  async function preload() {
    [latestProfile, latestAssessment] = await Promise.all([
      fetchProfile(user.id),
      fetchAssessment(user.id)
    ]);

    if (!latestProfile?.onboarding_completed || !latestAssessment) {
      routeTo("/onboarding-basic.html");
      return;
    }

    document.getElementById("welcome-copy").textContent =
      `${latestProfile.full_name || user.email} is set up for ${latestAssessment.body_part || "injury-aware"} adaptations.`;
  }

function buildTimestamps(rows) {
  return (rows || []).map((row) => ({
    time_range: formatTimestampRange(row),
    start_time: row.start_time ?? null,
    end_time: row.end_time ?? null,
    original: row.original ?? "",
    modified_alternative: row.modified_alternative ?? "",
    risk_flag: row.risk_flag ?? ""
  }));
}

/** Latest saved row for this YouTube video id (this user), or null. */
async function findCachedTimelineForUrl(supabase, userId, youtubeUrl) {
  const vid = extractYouTubeVideoId(youtubeUrl);
  if (!vid) return null;
  const { data, error } = await supabase
    .from("youtube_videos")
    .select("youtube_url, youtube_video_id, backend_payload, analysis_rows, video_title")
    .eq("user_id", userId)
    .eq("source", "youtube")
    .order("created_at", { ascending: false })
    .limit(80);
  if (error || !data?.length) return null;
  const row = data.find((r) => {
    const id = (r.youtube_video_id && String(r.youtube_video_id).trim()) || extractYouTubeVideoId(r.youtube_url || "");
    return id === vid;
  });
  if (!row) return null;
  return buildReuseVideoInformationForApi(row);
}

  document.getElementById("analyze-btn").addEventListener("click", async () => {
    const backendSessionId = readStorage(STORAGE_KEYS.backendSessionId) || latestAssessment?.backend_session_id;
    if (!backendSessionId) {
      setStatus(statusEl, "No backend session found. Re-save onboarding first.", "danger");
      return;
    }

    let payload;
    let label;
    if (source === "youtube") {
      const youtubeUrl = document.getElementById("youtube-url").value.trim();
      if (!youtubeUrl) {
        setStatus(statusEl, "Paste a YouTube URL before analyzing.", "danger");
        return;
      }
      payload = { session_id: backendSessionId, source: "youtube", youtube_url: youtubeUrl, output_format: "both" };
      label = youtubeUrl;
    } else {
      const workoutText = document.getElementById("workout-text").value.trim();
      if (!workoutText) {
        setStatus(statusEl, "Paste the workout text before analyzing.", "danger");
        return;
      }
      payload = { session_id: backendSessionId, source: "text", workout_text: workoutText, output_format: "both" };
      label = "Pasted workout";
    }

    try {
      let reuseVideoInformation = null;
      if (source === "youtube") {
        const url = document.getElementById("youtube-url").value.trim();
        reuseVideoInformation = await findCachedTimelineForUrl(supabase, user.id, url);
        if (reuseVideoInformation) {
          payload.reuse_video_information = reuseVideoInformation;
          setStatus(statusEl, "Using saved timestamps for this video — running adaptation…");
        } else {
          setStatus(statusEl, `Analyzing ${label}...`);
        }
      } else {
        setStatus(statusEl, `Analyzing ${label}...`);
      }

      const response = await analyzeWorkoutWithBackend(payload);

      const ytOrText =
        (payload.youtube_url && String(payload.youtube_url).trim()) ||
        (payload.workout_text && `Text: ${String(payload.workout_text).slice(0, 80)}…`) ||
        "Workout analysis";
      const playbackWorkout = buildAdaptFitPlaybackDocument(response.result_json || [], {
        youtubeUrl: response.youtube_url ?? payload.youtube_url,
        title: ytOrText
      });

      const canonicalYoutubeUrl = response.youtube_url ?? payload.youtube_url ?? "";
      const videoIdForRow = source === "youtube" ? extractYouTubeVideoId(canonicalYoutubeUrl) : "";

      const videoRecord = {
        user_id: user.id,
        source,
        youtube_url: canonicalYoutubeUrl || null,
        youtube_video_id: videoIdForRow || null,
        video_title: payload.youtube_url || "Manual workout entry",
        workout_text: payload.workout_text || null,
        backend_session_id: backendSessionId,
        video_timestamps: buildTimestamps(response.result_json),
        analysis_rows: response.result_json || [],
        markdown_table: response.result_markdown_table || "",
        backend_payload: {
          ...response,
          playback_workout: playbackWorkout,
          video_information: response.video_information ?? null
        }
      };

      const { data, error } = await supabase
        .from("youtube_videos")
        .insert(videoRecord)
        .select("id")
        .single();

      if (error) throw error;

      saveStorage(STORAGE_KEYS.latestVideoId, data.id);
      saveStorage(STORAGE_KEYS.latestResults, response);
      setStatus(statusEl, "Analysis saved. Opening results...", "success");
      routeTo(`/results.html?id=${data.id}`);
    } catch (error) {
      setStatus(statusEl, error.message || "Analysis failed.", "danger");
    }
  });

  await preload();
}
switchSource("youtube");
