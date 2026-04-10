import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { APP_CONFIG } from "./config.js";

export function hasSupabaseConfig() {
  return Boolean(APP_CONFIG.SUPABASE_URL && APP_CONFIG.SUPABASE_ANON_KEY);
}

export const supabase = hasSupabaseConfig()
  ? createClient(APP_CONFIG.SUPABASE_URL, APP_CONFIG.SUPABASE_ANON_KEY, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true
      }
    })
  : null;

export function requireSupabase() {
  if (!supabase) {
    throw new Error("Supabase is not configured. Copy values from assets/js/config.example.js into assets/js/config.js.");
  }
  return supabase;
}
