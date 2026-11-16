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
import GradientCard from "../components/GradientCard";
import { useAuth } from "../contexts/AuthContext";
import { colors, font, grad } from "../theme";

const STATUS_META = {
  published: { color: "#22c55e", bg: "#052e16", label: "PUBLISHED" },
  completed: { color: "#6366f1", bg: "#1e1b4b", label: "COMPLETED" },
  booked: { color: "#06c8d4", bg: "#0a2a2e", label: "BOOKED" },
  draft: { color: colors.textDim, bg: colors.surfaceAlt, label: "DRAFT" },
};

function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? STATUS_META.draft;
  return (
    <View style={[styles.badge, { backgroundColor: meta.bg, borderColor: meta.color + "55" }]}>
      <Text style={[styles.badgeText, { color: meta.color }]}>{meta.label}</Text>
    </View>
  );
}

export default function DashboardScreen({ navigation }) {
  const { user } = useAuth();
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
      setError("Could not load dashboard. Pull down to retry.");
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

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => fetchData(true)} tintColor={colors.gradStart} />
      }
    >
      {/* Hero header card */}
      <GradientCard style={styles.heroCard} barHeight={4}>
        <View style={styles.heroInner}>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroLabel}>ATHLETE</Text>
            <Text style={styles.heroName}>
              {athlete?.full_name || user?.full_name || "Athlete"}
            </Text>
            {enrollment && (
              <View style={styles.enrollPill}>
                <LinearGradient
                  colors={grad.subtle}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.enrollPillBg}
                />
                <Text style={styles.enrollText}>
                  {enrollment.sport_name} · {enrollment.center_name}
                </Text>
              </View>
            )}
          </View>
        </View>
      </GradientCard>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {/* Section header */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>Recent Assessments</Text>
        <Pressable onPress={() => navigation.navigate("Sessions")}>
          <Text style={styles.sectionLink}>View all →</Text>
        </Pressable>
      </View>

      {!data?.recent_sessions?.length ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No assessments yet.</Text>
        </View>
      ) : (
        data.recent_sessions.map((session) => (
          <GradientCard key={session.id}>
            <Pressable
              onPress={() => navigation.navigate("SessionDetail", { session_id: session.id })}
            >
              <View style={styles.sessionRow}>
                <Text style={styles.sessionDomain}>{session.domain_name}</Text>
                <StatusBadge status={session.status} />
              </View>
              <Text style={styles.sessionProtocol}>{session.protocol_name}</Text>
              <Text style={styles.sessionFramework}>{session.framework_name}</Text>
              <Text style={styles.sessionDate}>
                {new Date(session.assessed_on).toLocaleDateString("en-IN", {
                  day: "numeric", month: "short", year: "numeric",
                })}
              </Text>
            </Pressable>
          </GradientCard>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 18, paddingBottom: 52 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },

  heroCard: { marginBottom: 24 },
  heroInner: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" },
  heroLabel: { fontSize: font.xs, color: colors.gradStart, textTransform: "uppercase", letterSpacing: 2, marginBottom: 4 },
  heroName: { fontSize: font.xl, fontWeight: "700", color: colors.white },
  enrollPill: {
    marginTop: 10,
    alignSelf: "flex-start",
    borderRadius: 20,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.gradStart + "44",
  },
  enrollPillBg: { ...StyleSheet.absoluteFillObject },
  enrollText: { paddingHorizontal: 12, paddingVertical: 5, fontSize: font.xs, color: colors.gradStart },

  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  sectionLabel: {
    fontSize: font.xs,
    color: colors.textMuted,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    fontWeight: "600",
  },
  sectionLink: { fontSize: font.xs, color: colors.gradStart },

  sessionRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  sessionDomain: { fontSize: font.xs, color: colors.textDim, textTransform: "uppercase", letterSpacing: 0.5 },
  sessionProtocol: { fontSize: font.base, fontWeight: "700", color: colors.white },
  sessionFramework: { marginTop: 2, fontSize: font.sm, color: colors.textMuted },
  sessionDate: { marginTop: 8, fontSize: font.xs, color: colors.textDim },

  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 20,
    borderWidth: 1,
  },
  badgeText: { fontSize: 10, fontWeight: "700", letterSpacing: 0.5 },

  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: "dashed",
    padding: 28,
    alignItems: "center",
  },
  emptyText: { color: colors.textDim, fontSize: font.sm },
  error: { color: colors.red, fontSize: font.sm, marginBottom: 12 },
});
