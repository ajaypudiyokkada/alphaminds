import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { getDashboard } from "../api/athlete";
import { useAuth } from "../contexts/AuthContext";
import { colors, font, grad } from "../theme";

// ── Helpers ──────────────────────────────────────────────────────────────────

function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function calcAge(iso) {
  if (!iso) return null;
  const dob = new Date(iso);
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  if (
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate())
  ) age--;
  return age;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionCard({ title, children }) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.cardHeaderBar} />
        <Text style={styles.cardTitle}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

function InfoRow({ icon, label, value }) {
  if (!value) return null;
  return (
    <View style={styles.infoRow}>
      <View style={styles.infoIconWrap}>
        <Ionicons name={icon} size={15} color={colors.gradStart} />
      </View>
      <View style={styles.infoText}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
    </View>
  );
}

function EnrollmentStatusBadge({ status }) {
  const map = {
    active: { color: "#22c55e", bg: "#052e16", label: "ACTIVE" },
    inactive: { color: colors.textDim, bg: colors.surfaceAlt, label: "INACTIVE" },
    completed: { color: "#6366f1", bg: "#1e1b4b", label: "COMPLETED" },
  };
  const meta = map[status] ?? map.inactive;
  return (
    <View style={[styles.enrollBadge, { backgroundColor: meta.bg, borderColor: meta.color + "55" }]}>
      <Text style={[styles.enrollBadgeText, { color: meta.color }]}>{meta.label}</Text>
    </View>
  );
}

// ── Screen ────────────────────────────────────────────────────────────────────

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      setData(await getDashboard());
    } catch {
      setError("Could not load profile. Pull down to retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.gradStart} size="large" />
      </View>
    );
  }

  const athlete = data?.athlete;
  const enrollment = data?.primary_enrollment;
  const name = athlete?.full_name || user?.full_name || "Athlete";
  const age = calcAge(athlete?.date_of_birth);

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => fetchData(true)}
          tintColor={colors.gradStart}
        />
      }
    >
      {/* ── Avatar hero ── */}
      <View style={styles.heroWrap}>
        <LinearGradient
          colors={["#06c8d418", "#8b2fc912"]}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
        <LinearGradient colors={grad.accent} style={styles.avatarRing} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}>
          <View style={styles.avatarInner}>
            <Text style={styles.avatarText}>{initials(name)}</Text>
          </View>
        </LinearGradient>
        <Text style={styles.heroName}>{name}</Text>
        <View style={styles.heroTagRow}>
          <LinearGradient colors={grad.accentH} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.heroTagBar} />
          <Text style={styles.heroTag}>ATHLETE</Text>
          <LinearGradient colors={grad.accentH} start={{ x: 1, y: 0 }} end={{ x: 0, y: 0 }} style={styles.heroTagBar} />
        </View>
        {age !== null && (
          <Text style={styles.heroAge}>{age} years old</Text>
        )}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {/* ── Personal information ── */}
      <SectionCard title="Personal Information">
        <InfoRow icon="person-outline" label="Full Name" value={name} />
        <InfoRow icon="calendar-outline" label="Date of Birth"
          value={athlete?.date_of_birth ? `${formatDate(athlete.date_of_birth)}${age !== null ? `  ·  Age ${age}` : ""}` : null}
        />
        <InfoRow icon="male-female-outline" label="Gender" value={athlete?.gender_display || null} />
        <InfoRow icon="hand-left-outline" label="Dominant Hand"
          value={athlete?.dominant_hand
            ? athlete.dominant_hand.charAt(0).toUpperCase() + athlete.dominant_hand.slice(1)
            : null}
        />
      </SectionCard>

      {/* ── Contact ── */}
      <SectionCard title="Contact">
        <InfoRow icon="mail-outline" label="Email" value={athlete?.email || null} />
        <InfoRow icon="call-outline" label="Phone" value={athlete?.phone || null} />
      </SectionCard>

      {/* ── Current Enrollment ── */}
      {enrollment ? (
        <SectionCard title="Current Enrollment">
          <View style={styles.enrollHeader}>
            <View style={{ flex: 1 }}>
              <Text style={styles.enrollSport}>{enrollment.sport_name}</Text>
              <Text style={styles.enrollCenter}>{enrollment.center_name}</Text>
            </View>
            <EnrollmentStatusBadge status={enrollment.status} />
          </View>
          {enrollment.batch_name ? (
            <View style={styles.batchPill}>
              <Text style={styles.batchText}>{enrollment.batch_name}</Text>
            </View>
          ) : null}
          <View style={styles.enrollDates}>
            <View style={styles.enrollDateItem}>
              <Text style={styles.enrollDateLabel}>Enrolled</Text>
              <Text style={styles.enrollDateValue}>{formatDate(enrollment.start_date)}</Text>
            </View>
            {enrollment.end_date && (
              <View style={styles.enrollDateItem}>
                <Text style={styles.enrollDateLabel}>Until</Text>
                <Text style={styles.enrollDateValue}>{formatDate(enrollment.end_date)}</Text>
              </View>
            )}
          </View>
        </SectionCard>
      ) : (
        <SectionCard title="Enrollment">
          <Text style={styles.noEnrollText}>No active enrollment on record.</Text>
        </SectionCard>
      )}

      {/* ── Sign out ── */}
      <Pressable style={styles.signOutBtn} onPress={logout}>
        <Ionicons name="log-out-outline" size={18} color="#f87171" />
        <Text style={styles.signOutText}>Sign Out</Text>
      </Pressable>
    </ScrollView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const AVATAR_SIZE = 80;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { paddingBottom: 60 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },

  // Hero
  heroWrap: {
    alignItems: "center",
    paddingTop: 36,
    paddingBottom: 28,
    paddingHorizontal: 24,
    overflow: "hidden",
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    marginBottom: 20,
  },
  avatarRing: {
    width: AVATAR_SIZE + 4,
    height: AVATAR_SIZE + 4,
    borderRadius: (AVATAR_SIZE + 4) / 2,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 14,
  },
  avatarInner: {
    width: AVATAR_SIZE,
    height: AVATAR_SIZE,
    borderRadius: AVATAR_SIZE / 2,
    backgroundColor: colors.surface,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: { fontSize: font["2xl"], fontWeight: "700", color: colors.white },
  heroName: { fontSize: font.xl, fontWeight: "800", color: colors.white, marginBottom: 8 },
  heroTagRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 6 },
  heroTagBar: { width: 24, height: 1.5, borderRadius: 1 },
  heroTag: { fontSize: font.xs, color: colors.gradStart, letterSpacing: 3, fontWeight: "700" },
  heroAge: { fontSize: font.sm, color: colors.textMuted, marginTop: 2 },

  // Section card
  card: {
    marginHorizontal: 16,
    marginBottom: 14,
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  cardHeaderBar: {
    width: 3,
    height: 14,
    borderRadius: 2,
    backgroundColor: colors.gradStart,
  },
  cardTitle: { fontSize: font.sm, fontWeight: "700", color: colors.white, letterSpacing: 0.3 },

  // Info rows
  infoRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border + "55",
  },
  infoIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: colors.gradStart + "15",
    justifyContent: "center",
    alignItems: "center",
    marginTop: 1,
  },
  infoText: { flex: 1 },
  infoLabel: { fontSize: font.xs, color: colors.textDim, marginBottom: 2 },
  infoValue: { fontSize: font.sm, color: colors.white, lineHeight: 20 },

  // Enrollment
  enrollHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
    gap: 10,
  },
  enrollSport: { fontSize: font.base, fontWeight: "700", color: colors.white, marginBottom: 2 },
  enrollCenter: { fontSize: font.sm, color: colors.textMuted },
  enrollBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 20,
    borderWidth: 1,
    alignSelf: "flex-start",
  },
  enrollBadgeText: { fontSize: 10, fontWeight: "700", letterSpacing: 0.5 },
  batchPill: {
    marginHorizontal: 16,
    marginBottom: 10,
    alignSelf: "flex-start",
    backgroundColor: colors.gradStart + "15",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: colors.gradStart + "30",
  },
  batchText: { fontSize: font.xs, color: colors.gradStart },
  enrollDates: {
    flexDirection: "row",
    gap: 24,
    paddingHorizontal: 16,
    paddingBottom: 14,
  },
  enrollDateItem: {},
  enrollDateLabel: { fontSize: font.xs, color: colors.textDim, marginBottom: 2 },
  enrollDateValue: { fontSize: font.sm, color: colors.white },
  noEnrollText: { padding: 16, fontSize: font.sm, color: colors.textDim },

  // Sign out
  signOutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#7f1d1d",
    backgroundColor: "#2a0a0a",
  },
  signOutText: { fontSize: font.base, fontWeight: "700", color: "#f87171" },

  error: { color: colors.red, fontSize: font.sm, marginHorizontal: 16, marginBottom: 12 },
});
