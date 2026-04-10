import { requireSupabase } from "./supabase-client.js";
import { routeTo } from "./state.js";

export async function getCurrentSession() {
  const client = requireSupabase();
  const { data, error } = await client.auth.getSession();
  if (error) throw error;
  return data.session;
}

export async function getCurrentUser() {
  const session = await getCurrentSession();
  return session?.user ?? null;
}

export async function requireUser(redirect = "/index.html") {
  const user = await getCurrentUser();
  if (!user) {
    routeTo(redirect);
    return null;
  }
  return user;
}

export async function fetchProfile(userId) {
  const client = requireSupabase();
  const { data, error } = await client
    .from("users")
    .select("*")
    .eq("id", userId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function fetchAssessment(userId) {
  const client = requireSupabase();
  const { data, error } = await client
    .from("injury_assessments")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function signOut() {
  const client = requireSupabase();
  const { error } = await client.auth.signOut();
  if (error) throw error;
  routeTo("/index.html");
}
