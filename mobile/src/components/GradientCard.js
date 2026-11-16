import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { colors, grad } from "../theme";

/**
 * A card with the signature cyan→violet gradient bar at the bottom.
 * Props:
 *   style      — outer container overrides
 *   barHeight  — gradient bar height (default 3)
 *   children
 */
export default function GradientCard({ style, barHeight = 3, children }) {
  return (
    <View style={[styles.card, style]}>
      <View style={styles.body}>{children}</View>
      <LinearGradient
        colors={grad.accent}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={[styles.bar, { height: barHeight }]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
    marginBottom: 12,
  },
  body: { padding: 18 },
  bar: { width: "100%" },
});
