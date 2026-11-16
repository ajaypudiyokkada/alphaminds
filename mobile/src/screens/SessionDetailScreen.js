import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { getSessionDetail } from "../api/athlete";
import GradientCard from "../components/GradientCard";
import { colors, font, grad } from "../theme";

function MetricRow({ metric, index }) {
  return (
    <View style={[styles.metricRow, index === 0 && { borderTopWidth: 0 }]}>
      <Text style={styles.metricLabel}>
        {metric.metric_label || metric.metric_name}
      </Text>
      <View style={styles.metricRight}>
        <Text style={styles.metricValue}>{metric.display_value}</Text>
        {metric.units ? <Text style={styles.metricUnit}>{metric.units}</Text> : null}
      </View>
    </View>
  );
}

export default function SessionDetailScreen({ route }) {
  const { session_id } = route.params;
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getSessionDetail(session_id)
      .then(setSession)
      .catch(() => setError("Could not load session details."))
      .finally(() => setLoading(false));
  }, [session_id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.gradStart} size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  // Both published and completed sessions are viewable results.
  const isViewable = session.status === "published" || session.status === "completed";

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>

      {/* Hero */}
      <GradientCard barHeight={4}>
        <Text style={styles.domain}>{session.domain_name}</Text>
        <Text style={styles.protocol}>{session.protocol_name}</Text>
        <Text style={styles.framework}>{session.framework_name}</Text>

        <View style={styles.metaRow}>
          <MetaChip label="Sport" value={session.sport_name} />
          <View style={styles.metaDivider} />
          <MetaChip
            label="Date"
            value={new Date(session.assessed_on).toLocaleDateString("en-IN", {
              day: "numeric", month: "short", year: "numeric",
            })}
          />
          <View style={styles.metaDivider} />
          <MetaChip
            label="Status"
            value={session.status.toUpperCase()}
            valueColor={session.status === "published" ? "#22c55e" : "#6366f1"}
          />
        </View>
      </GradientCard>

      {/* Notes */}
      {session.notes ? (
        <GradientCard>
          <Text style={styles.sectionLabel}>Notes</Text>
          <Text style={styles.notesText}>{session.notes}</Text>
        </GradientCard>
      ) : null}

      {/* Metrics */}
      {isViewable ? (
        <View style={styles.metricsSection}>
          <View style={styles.metricsTitleRow}>
            <LinearGradient
              colors={grad.accentH}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.titleBar}
            />
            <Text style={styles.metricsTitle}>Assessment Results</Text>
          </View>

          <View style={styles.metricsCard}>
            {session.metric_values.length === 0 ? (
              <Text style={styles.noMetrics}>
                {session.status === "completed" ? "Detailed results will appear here once they are published." : "No metrics captured."}
              </Text>
            ) : (
              session.metric_values.map((m, i) => (
                <MetricRow key={m.id} metric={m} index={i} />
              ))
            )}
            <LinearGradient
              colors={grad.accent}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.metricsBar}
            />
          </View>
        </View>
      ) : (
        <View style={styles.lockedCard}>
          <LinearGradient colors={grad.subtle} style={StyleSheet.absoluteFill} />
          <Text style={styles.lockedIcon}>🔒</Text>
          <Text style={styles.lockedTitle}>Results Pending</Text>
          <Text style={styles.lockedBody}>
            Your coach will publish results once the assessment review is complete.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

function MetaChip({ label, value, valueColor }) {
  return (
    <View style={styles.metaChip}>
      <Text style={styles.metaLabel}>{label}</Text>
      <Text style={[styles.metaValue, valueColor && { color: valueColor }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 18, paddingBottom: 52 },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },

  domain: { fontSize: font.xs, color: colors.gradStart, textTransform: "uppercase", letterSpacing: 2, marginBottom: 6 },
  protocol: { fontSize: font["2xl"], fontWeight: "800", color: colors.white },
  framework: { marginTop: 4, fontSize: font.sm, color: colors.textMuted },

  metaRow: {
    flexDirection: "row",
    marginTop: 18,
    backgroundColor: colors.surfaceAlt,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  metaChip: { flex: 1, padding: 12, alignItems: "center" },
  metaDivider: { width: 1, backgroundColor: colors.border },
  metaLabel: { fontSize: font.xs, color: colors.textDim, marginBottom: 4 },
  metaValue: { fontSize: font.sm, color: colors.white, fontWeight: "700", textAlign: "center" },

  sectionLabel: { fontSize: font.xs, color: colors.textDim, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  notesText: { fontSize: font.sm, color: colors.textMuted, lineHeight: 22 },

  metricsSection: { marginTop: 8 },
  metricsTitleRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 12 },
  titleBar: { width: 3, height: 18, borderRadius: 2 },
  metricsTitle: { fontSize: font.xs, color: colors.textMuted, textTransform: "uppercase", letterSpacing: 1.5, fontWeight: "600" },

  metricsCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 18,
    paddingVertical: 15,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  metricLabel: { flex: 1, fontSize: font.sm, color: colors.textMuted },
  metricRight: { flexDirection: "row", alignItems: "baseline", gap: 4 },
  metricValue: { fontSize: font.base, fontWeight: "700", color: colors.white },
  metricUnit: { fontSize: font.xs, color: colors.textDim },
  noMetrics: { color: colors.textDim, fontSize: font.sm, padding: 18 },
  metricsBar: { height: 3 },

  lockedCard: {
    marginTop: 8,
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.gradEnd + "33",
    padding: 28,
    alignItems: "center",
    overflow: "hidden",
  },
  lockedIcon: { fontSize: 28, marginBottom: 12 },
  lockedTitle: { fontSize: font.base, fontWeight: "700", color: colors.white, marginBottom: 8 },
  lockedBody: { fontSize: font.sm, color: colors.textMuted, textAlign: "center", lineHeight: 22 },

  errorText: { color: colors.red, fontSize: font.sm },
});
