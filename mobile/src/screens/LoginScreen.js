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
import { useAuth } from "../contexts/AuthContext";
import { colors, font, grad } from "../theme";

export default function LoginScreen({ navigation }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleLogin() {
    Keyboard.dismiss();
    if (!username.trim() || !password.trim()) {
      setError("Please enter your username and password.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (e) {
      if (!e.response) {
        setError("Cannot reach server. Check your connection.");
      } else {
        setError(e.response.data?.detail || "Invalid credentials. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior="padding"
      keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 30}
    >
      <LinearGradient
        colors={["#06c8d418", "#8b2fc912", "#0c0d11"]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />

      <ScrollView
        contentContainerStyle={styles.inner}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        onScrollBeginDrag={Keyboard.dismiss}
      >
        {/* Brand */}
        <View style={styles.brandRow}>
          <LinearGradient colors={grad.accentH} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.logoBar} />
          <Text style={styles.brand}>AlphaMinds</Text>
        </View>
        <Text style={styles.tagline}>Athlete Intelligence Platform</Text>

        {/* Card — content + bar as siblings inside overflow:hidden wrapper */}
        <View style={styles.card}>
          <View style={styles.cardContent}>
            {error ? <Text style={styles.error}>{error}</Text> : null}

            <Text style={styles.label}>Username</Text>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
              placeholderTextColor={colors.textDim}
              placeholder="your.username"
            />

            <Text style={[styles.label, { marginTop: 16 }]}>Password</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.inputFlex}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                placeholderTextColor={colors.textDim}
                placeholder="••••••••"
              />
              <Pressable onPress={() => setShowPassword((v) => !v)} style={styles.eyeBtn} hitSlop={8}>
                <Ionicons
                  name={showPassword ? "eye-outline" : "eye-off-outline"}
                  size={20}
                  color={colors.textDim}
                />
              </Pressable>
            </View>

            <Pressable onPress={() => navigation.navigate("ForgotPassword")} style={styles.forgotLink}>
              <Text style={styles.forgotText}>Forgot password?</Text>
            </Pressable>

            <Pressable
              style={[styles.btnWrap, loading && { opacity: 0.6 }]}
              onPress={handleLogin}
              disabled={loading}
            >
              <LinearGradient
                colors={grad.accent}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.btn}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.btnText}>Sign In</Text>
                )}
              </LinearGradient>
            </Pressable>
          </View>

          {/* Gradient bar sits outside cardContent padding so it hugs the bottom */}
          <LinearGradient
            colors={grad.accent}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.cardBar}
          />
        </View>

        {/* Sign Up */}
        <Pressable onPress={() => navigation.navigate("SignUp")} style={styles.signupRow}>
          <Text style={styles.signupText}>New athlete? </Text>
          <Text style={styles.signupLink}>Get in touch →</Text>
        </Pressable>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  inner: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 80,
    paddingBottom: 48,
  },
  brandRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 6 },
  logoBar: { width: 4, height: 28, borderRadius: 2 },
  brand: { fontSize: font["2xl"], fontWeight: "800", color: colors.white, letterSpacing: 0.5 },
  tagline: {
    fontSize: font.xs,
    color: colors.textMuted,
    textTransform: "uppercase",
    letterSpacing: 2,
    marginBottom: 36,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: "hidden",
  },
  cardContent: {
    padding: 22,
  },
  label: { fontSize: font.sm, color: colors.textMuted, marginBottom: 8 },
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
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceAlt,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
  },
  inputFlex: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: colors.white,
    fontSize: font.base,
  },
  eyeBtn: { paddingHorizontal: 14 },
  btnWrap: { marginTop: 24, marginBottom: 8 },
  btn: { borderRadius: 12, paddingVertical: 15, alignItems: "center" },
  btnText: { fontSize: font.base, fontWeight: "700", color: "#fff", letterSpacing: 0.3 },
  cardBar: { height: 3 },
  forgotLink: { alignSelf: "flex-end", marginTop: 10 },
  forgotText: { fontSize: font.sm, color: colors.gradStart },
  signupRow: { flexDirection: "row", justifyContent: "center", marginTop: 24 },
  signupText: { fontSize: font.sm, color: colors.textMuted },
  signupLink: { fontSize: font.sm, color: colors.gradStart, fontWeight: "600" },
  error: {
    color: "#f87171",
    fontSize: font.sm,
    backgroundColor: "#2a0a0a",
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#7f1d1d",
  },
});
