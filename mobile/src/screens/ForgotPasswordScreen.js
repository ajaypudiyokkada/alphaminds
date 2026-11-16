import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { forgotPassword } from "../api/auth";
import { colors, font, grad } from "../theme";

export default function ForgotPasswordScreen({ navigation }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    Keyboard.dismiss();
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email.trim());
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <View style={styles.root}>
        <LinearGradient colors={["#06c8d418", "#8b2fc912", "#0c0d11"]} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
        <View style={styles.successInner}>
          <LinearGradient colors={grad.accent} style={styles.iconWrap}>
            <Ionicons name="mail-outline" size={28} color="#fff" />
          </LinearGradient>
          <Text style={styles.successTitle}>Check your inbox</Text>
          <Text style={styles.successBody}>
            If an account is linked to{" "}
            <Text style={{ color: colors.gradStart }}>{email}</Text>
            {", a password reset link has been sent."}
          </Text>
          <Pressable style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backBtnText}>← Back to Sign In</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior="padding"
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 30}
    >
      <LinearGradient colors={["#06c8d418", "#8b2fc912", "#0c0d11"]} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />

      <ScrollView contentContainerStyle={styles.inner} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>

        <Pressable onPress={() => navigation.goBack()} style={styles.backLink}>
          <Ionicons name="arrow-back" size={18} color={colors.gradStart} />
          <Text style={styles.backLinkText}>Back to Sign In</Text>
        </Pressable>

        <Text style={styles.title}>Forgot Password?</Text>
        <Text style={styles.subtitle}>
          Enter the email linked to your account and we'll send you a reset link.
        </Text>

        <View style={styles.card}>
          <View style={styles.cardContent}>
            {error ? <Text style={styles.error}>{error}</Text> : null}

            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="done"
              onSubmitEditing={handleSubmit}
              placeholderTextColor={colors.textDim}
              placeholder="your@email.com"
            />

            <Pressable
              style={[styles.btnWrap, loading && { opacity: 0.6 }]}
              onPress={handleSubmit}
              disabled={loading}
            >
              <LinearGradient colors={grad.accent} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.btn}>
                {loading
                  ? <ActivityIndicator color="#fff" />
                  : <Text style={styles.btnText}>Send Reset Link</Text>
                }
              </LinearGradient>
            </Pressable>
          </View>
          <LinearGradient colors={grad.accent} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.cardBar} />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  inner: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 60, paddingBottom: 48 },
  backLink: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 32 },
  backLinkText: { fontSize: font.sm, color: colors.gradStart },
  title: { fontSize: font["2xl"], fontWeight: "800", color: colors.white, marginBottom: 8 },
  subtitle: { fontSize: font.sm, color: colors.textMuted, lineHeight: 22, marginBottom: 32 },
  label: { fontSize: font.sm, color: colors.textMuted, marginBottom: 8 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  cardContent: { padding: 22 },
  input: {
    backgroundColor: colors.surfaceAlt,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: colors.white,
    fontSize: font.base,
  },
  btnWrap: { marginTop: 24, marginBottom: 8 },
  btn: { borderRadius: 12, paddingVertical: 15, alignItems: "center" },
  btnText: { fontSize: font.base, fontWeight: "700", color: "#fff" },
  cardBar: { height: 3 },
  error: {
    color: "#f87171", fontSize: font.sm, backgroundColor: "#2a0a0a",
    borderRadius: 8, padding: 10, marginBottom: 16,
    borderWidth: 1, borderColor: "#7f1d1d",
  },
  // Success state
  successInner: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  iconWrap: { width: 68, height: 68, borderRadius: 34, justifyContent: "center", alignItems: "center", marginBottom: 20 },
  successTitle: { fontSize: font.xl, fontWeight: "800", color: colors.white, marginBottom: 12 },
  successBody: { fontSize: font.sm, color: colors.textMuted, textAlign: "center", lineHeight: 24, marginBottom: 32 },
  backBtn: { borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 24 },
  backBtnText: { fontSize: font.sm, color: colors.textMuted },
});
