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
import { getSessions } from "../api/athlete";
import GradientCard from "../components/GradientCard";
import { colors, font } from "../theme";

const STATUS_META = {
  published: { color: "#22c55e", bg: "#052e16" },
  completed: { color: "#6366f1", bg: "#1e1b4b" },
  booked: { color: "#06c8d4", bg: "#0a2a2e" },
  draft: { color: colors.textDim, bg: colors.surfaceAlt },
  cancelled: { color: colors.red, bg: "#2a0a0a" },
};

export default function SessionListScreen({ navigation }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const fetchSessions = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      setSessions(await getSessions());
    } catch {
      setError("Could not load sessions.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchSessions(); }, [fetchSessions]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.gradStart} size="large" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => fetchSessions(true)} tintColor={colors.gradStart} />
      }
    >
      <Text style={styles.title}>Assessments</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {sessions.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No assessment sessions yet.</Text>
        </View>
      ) : (
        sessions.map((session) => {
          const meta = STATUS_META[session.status] ?? STATUS_META.draft;
          return (
            <GradientCard key={session.id}>
              <Pressable
                onPress={() => navigation.navigate("SessionDetail", { session_id: session.id })}
              >
                <View style={styles.row}>
                  <Text style={styles.domain}>{session.domain_name}</Text>
                  <View style={[styles.badge, { backgroundColor: meta.bg, borderColor: meta.color + "55" }]}>
                    <Text style={[styles.badgeText, { color: meta.color }]}>
                      {session.status.toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={styles.protocol}>{session.protocol_name}</Text>
                <Text style={styles.framework}>{session.framework_name}</Text>
                <View style={styles.footer}>
                  <Text style={styles.date}>
                    {new Date(session.assessed_on).toLocaleDateString("en-IN", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </Text>
                  <Text style={styles.arrow}>→</Text>
                </View>
              </Pressable>
            </GradientCard>
          );
        })
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 18, paddingBottom: 52 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },
  title: { fontSize: font.xl, fontWeight: "700", color: colors.white, marginBottom: 20 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  domain: { fontSize: font.xs, color: colors.textDim, textTransform: "uppercase", letterSpacing: 0.5 },
  protocol: { fontSize: font.base, fontWeight: "700", color: colors.white },
  framework: { marginTop: 2, fontSize: font.sm, color: colors.textMuted },
  footer: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 10 },
  date: { fontSize: font.xs, color: colors.textDim },
  arrow: { color: colors.gradStart, fontSize: font.sm },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 20, borderWidth: 1 },
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
