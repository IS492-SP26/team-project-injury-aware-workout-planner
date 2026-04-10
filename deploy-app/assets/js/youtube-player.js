/**
 * YouTube IFrame API loader + player with periodic current-time callbacks.
 * Includes: race-safe API load, iframe embed fallback if the API player fails.
 */

let iframeApiPromise = null;

export function loadYouTubeIframeApi() {
  if (window.YT && window.YT.Player) {
    return Promise.resolve(window.YT);
  }
  if (!iframeApiPromise) {
    iframeApiPromise = new Promise((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        if (window.YT && window.YT.Player) {
          settled = true;
          resolve(window.YT);
        }
      };

      const existing = document.querySelector('script[src*="youtube.com/iframe_api"]');
      const previousReady = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (typeof previousReady === "function") previousReady();
        finish();
      };

      if (!existing) {
        const tag = document.createElement("script");
        tag.src = "https://www.youtube.com/iframe_api";
        tag.async = true;
        document.head.appendChild(tag);
      }

      // Race: cached script can finish before our onYouTubeIframeAPIReady assignment.
      const poll = window.setInterval(finish, 32);
      window.setTimeout(() => {
        window.clearInterval(poll);
        finish();
      }, 15000);
    });
  }
  return iframeApiPromise;
}

/**
 * Plain embed — always renders something visible; used if YT.Player fails.
 */
export function mountYoutubeEmbed(container, videoId) {
  if (!container || !videoId) return;
  container.innerHTML = "";
  const iframe = document.createElement("iframe");
  iframe.src = `https://www.youtube.com/embed/${encodeURIComponent(videoId)}?rel=0`;
  iframe.title = "YouTube workout";
  iframe.setAttribute("loading", "lazy");
  iframe.style.cssText = "width:100%;height:100%;min-height:min(560px,68vh);border:0;border-radius:22px;";
  iframe.allow =
    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
  iframe.setAttribute("allowfullscreen", "");
  container.appendChild(iframe);
}

/**
 * @param {HTMLElement} mountEl — must have a non-empty `id` for YT.Player (most reliable).
 * @returns {{ destroy: () => void, usedEmbed: () => boolean }}
 */
export function createPollingPlayer(mountEl, videoId, options = {}) {
  const intervalMs = options.intervalMs ?? 500;
  const onSecond = options.onSecond;
  const onFallbackEmbed = options.onFallbackEmbed;

  let player = null;
  let poller = null;
  let lastSecond = -1;
  let usedEmbed = false;

  function report() {
    if (!player || typeof player.getCurrentTime !== "function") return;
    const second = Math.floor(player.getCurrentTime() || 0);
    if (second !== lastSecond) {
      lastSecond = second;
      if (typeof onSecond === "function") onSecond(second);
    }
  }

  function startPolling() {
    if (poller) clearInterval(poller);
    poller = window.setInterval(report, intervalMs);
  }

  function destroy() {
    if (poller) {
      clearInterval(poller);
      poller = null;
    }
    try {
      if (player && typeof player.destroy === "function") player.destroy();
    } catch {
      /* ignore */
    }
    player = null;
    mountEl.innerHTML = "";
  }

  const playerId = mountEl.id || `yt-mount-${Date.now()}`;
  if (!mountEl.id) mountEl.id = playerId;

  loadYouTubeIframeApi()
    .then((YT) => {
      try {
        player = new YT.Player(playerId, {
          videoId,
          playerVars: { rel: 0, modestbranding: 1 },
          events: {
            onReady: () => {
              report();
              startPolling();
            },
            onStateChange: () => report(),
            onError: () => {
              destroy();
              usedEmbed = true;
              mountYoutubeEmbed(mountEl, videoId);
              if (typeof onFallbackEmbed === "function") onFallbackEmbed();
            }
          }
        });
      } catch {
        usedEmbed = true;
        mountYoutubeEmbed(mountEl, videoId);
        if (typeof onFallbackEmbed === "function") onFallbackEmbed();
      }
    })
    .catch(() => {
      usedEmbed = true;
      mountYoutubeEmbed(mountEl, videoId);
      if (typeof onFallbackEmbed === "function") onFallbackEmbed();
    });

  return {
    destroy,
    usedEmbed: () => usedEmbed
  };
}

/**
 * Extract video id from common YouTube URL shapes (optional www / m. host).
 */
export function extractYouTubeVideoId(url) {
  if (!url || typeof url !== "string") return "";
  const u = url.trim();
  const host = "(?:https?:\\/\\/)?(?:www\\.|m\\.)?";
  const patterns = [
    new RegExp(`${host}youtube\\.com\\/watch\\?[^#]*[&?]v=([a-zA-Z0-9_-]{6,})`),
    new RegExp(`${host}youtube\\.com\\/watch\\?v=([a-zA-Z0-9_-]{6,})`),
    new RegExp(`${host}youtu\\.be\\/([a-zA-Z0-9_-]{6,})`),
    new RegExp(`${host}youtube\\.com\\/embed\\/([a-zA-Z0-9_-]{6,})`),
    new RegExp(`${host}youtube\\.com\\/shorts\\/([a-zA-Z0-9_-]{6,})`),
    new RegExp(`${host}youtube\\.com\\/live\\/([a-zA-Z0-9_-]{6,})`),
    /[?&#]v=([a-zA-Z0-9_-]{6,})/
  ];
  for (const re of patterns) {
    const m = u.match(re);
    if (m && m[1]) return m[1].split("&", 1)[0];
  }
  return "";
}
