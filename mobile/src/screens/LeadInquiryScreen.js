import DateTimePicker from "@react-native-community/datetimepicker";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { submitLead } from "../api/leads";
import { colors, font, grad } from "../theme";

// ── Constants ────────────────────────────────────────────────────────────────

const INQUIRY_TYPES = [
  { value: "athlete_mental_toughness", label: "Personality & Mental Toughness" },
  { value: "athlete_cognitive_vision", label: "Cognitive Vision Evaluation" },
  { value: "athlete_emotional_regulation", label: "Emotional Regulation Program" },
  { value: "academy_partnership", label: "Academy — Explore AlphaMinds" },
];

const ATHLETE_TYPES = INQUIRY_TYPES.filter((t) =>
  ["athlete_mental_toughness", "athlete_cognitive_vision", "athlete_emotional_regulation"].includes(t.value)
);

const isAthleteType = (t) =>
  ["athlete_mental_toughness", "athlete_cognitive_vision", "athlete_emotional_regulation"].includes(t);

const GENDER_OPTIONS = [
  { value: "M", label: "Male" },
  { value: "F", label: "Female" },
  { value: "O", label: "Other" },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function calcAge(dob) {
  if (!dob) return null;
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  if (
    today.getMonth() < dob.getMonth() ||
    (today.getMonth() === dob.getMonth() && today.getDate() < dob.getDate())
  ) age--;
  return age;
}

function toISODate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatDisplayDate(d) {
  if (!d) return null;
  return `${String(d.getDate()).padStart(2, "0")} / ${String(d.getMonth() + 1).padStart(2, "0")} / ${d.getFullYear()}`;
}

// ── Pincode lookup (India) ───────────────────────────────────────────────────

async function lookupPincode(pin) {
  try {
    const res = await fetch(`https://api.postalpincode.in/pincode/${pin}`);
    const json = await res.json();
    if (json?.[0]?.Status === "Success") {
      const po = json[0].PostOffice?.[0];
      if (po) return { city: po.District, state: po.State };
    }
  } catch {}
  return null;
}

// ── Screen ───────────────────────────────────────────────────────────────────

export default function LeadInquiryScreen({ route }) {
  const athleteOnly = route?.params?.athleteOnly ?? false;
  const visibleTypes = athleteOnly ? ATHLETE_TYPES : INQUIRY_TYPES;

  const [types, setTypes] = useState([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [mobile, setMobile] = useState("");
  const [gender, setGender] = useState("");
  const [dob, setDob] = useState(null);       // Date | null
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [tempDate, setTempDate] = useState(null); // iOS staging
  const [parentMobile, setParentMobile] = useState("");
  const [pincode, setPincode] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [pincodeStatus, setPincodeStatus] = useState("idle"); // idle | loading | found | notfound
  const [sport, setSport] = useState("");
  const [academyName, setAcademyName] = useState("");
  const [academyCity, setAcademyCity] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errors, setErrors] = useState({});

  const age = calcAge(dob);
  const isMinor = age !== null && age < 18;
  const hasAthlete = types.some(isAthleteType);
  const hasAcademy = types.includes("academy_partnership");

  // Auto-lookup pincode when 6 digits entered
  useEffect(() => {
    if (pincode.length !== 6) {
      if (pincodeStatus !== "idle") {
        setPincodeStatus("idle");
        setCity("");
        setState("");
      }
      return;
    }
    let cancelled = false;
    setPincodeStatus("loading");
    setCity("");
    setState("");
    lookupPincode(pincode).then((result) => {
      if (cancelled) return;
      if (result) {
        setCity(result.city);
        setState(result.state);
        setPincodeStatus("found");
      } else {
        setPincodeStatus("notfound");
      }
    });
    return () => { cancelled = true; };
  }, [pincode]);

  function toggleType(val) {
    setTypes((prev) =>
      prev.includes(val) ? prev.filter((t) => t !== val) : [...prev, val]
    );
  }

  async function handleSubmit() {
    const errs = {};
    if (types.length === 0) errs.types = "Please select at least one interest.";
    if (!fullName.trim()) errs.fullName = "Name is required.";
    if (!email.trim()) errs.email = "Email is required.";
    if (!mobile.trim()) errs.mobile = "Mobile number is required.";
    if (isMinor && !parentMobile.trim()) errs.parent_mobile = "Parent/guardian mobile is required for under-18.";
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setErrors({});
    setLoading(true);
    try {
      await submitLead({
        inquiry_types: types,
        full_name: fullName.trim(),
        email: email.trim(),
        mobile_number: mobile.trim(),
        gender,
        date_of_birth: dob ? toISODate(dob) : null,
        parent_mobile: parentMobile.trim(),
        pincode: pincode.trim(),
        city: city.trim(),
        state: state.trim(),
        athlete_sport: hasAthlete ? sport.trim() : "",
        academy_name: hasAcademy ? academyName.trim() : "",
        academy_city: hasAcademy ? academyCity.trim() : "",
        message: message.trim(),
      });
      setSuccess(true);
    } catch (e) {
      const detail = e.response?.data;
      setErrors(
        detail && typeof detail === "object"
          ? detail
          : { non_field: "Submission failed. Please try again." }
      );
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setSuccess(false);
    setTypes([]); setFullName(""); setEmail(""); setMobile("");
    setGender(""); setDob(null); setTempDate(null); setParentMobile("");
    setPincode(""); setCity(""); setState(""); setPincodeStatus("idle");
    setSport(""); setAcademyName(""); setAcademyCity(""); setMessage("");
    setErrors({});
  }

  // ── Success state ──────────────────────────────────────────────────────────
  if (success) {
    return (
      <View style={styles.successRoot}>
        <LinearGradient colors={grad.subtle} style={StyleSheet.absoluteFill} />
        <LinearGradient colors={grad.accent} style={styles.successIconWrap}>
          <Text style={styles.successIcon}>✓</Text>
        </LinearGradient>
        <Text style={styles.successTitle}>Enquiry Received</Text>
        <Text style={styles.successBody}>
          Thank you! Our team will connect with you shortly.
        </Text>
        <Pressable style={styles.btnWrap} onPress={resetForm}>
          <LinearGradient colors={grad.accent} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.btn}>
            <Text style={styles.btnText}>Submit Another</Text>
          </LinearGradient>
        </Pressable>
      </View>
    );
  }

  // ── Form ───────────────────────────────────────────────────────────────────
  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: colors.bg }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.pageTitle}>Get in Touch</Text>
        <Text style={styles.pageSubtitle}>
          Tell us what you're looking for and we'll reach out.
        </Text>

        {errors.non_field ? (
          <Text style={styles.errorBanner}>{errors.non_field}</Text>
        ) : null}

        {/* ── Interest — multi-select ── */}
        <Text style={styles.label}>
          I'm interested in <Text style={styles.required}>*</Text>
          {"  "}<Text style={styles.labelHint}>select all that apply</Text>
        </Text>
        <View style={styles.typeGrid}>
          {visibleTypes.map((t) => {
            const active = types.includes(t.value);
            return (
              <Pressable
                key={t.value}
                style={[styles.typeChip, active && styles.typeChipActive]}
                onPress={() => toggleType(t.value)}
              >
                {active && (
                  <LinearGradient colors={grad.subtle} style={StyleSheet.absoluteFill} borderRadius={12} />
                )}
                <View style={styles.typeChipRow}>
                  <View style={[styles.checkbox, active && styles.checkboxActive]}>
                    {active && <Text style={styles.checkmark}>✓</Text>}
                  </View>
                  <Text style={[styles.typeChipText, active && styles.typeChipTextActive]}>
                    {t.label}
                  </Text>
                </View>
              </Pressable>
            );
          })}
        </View>
        {(errors.types || errors.inquiry_types) ? (
          <Text style={styles.fieldError}>{errors.types || (Array.isArray(errors.inquiry_types) ? errors.inquiry_types[0] : errors.inquiry_types)}</Text>
        ) : null}

        {/* ── Identity ── */}
        <Field label="Full Name" required value={fullName} onChange={setFullName} error={errors.full_name || errors.fullName} />
        <Field label="Email" required value={email} onChange={setEmail} keyboardType="email-address" error={errors.email} />
        <Field
          label="Mobile"
          required
          value={mobile}
          onChange={setMobile}
          keyboardType="phone-pad"
          placeholder="+91 9XXXXXXXXX"
          error={errors.mobile_number || errors.mobile}
        />

        {/* ── Gender ── */}
        <Text style={styles.label}>Gender</Text>
        <View style={styles.pillRow}>
          {GENDER_OPTIONS.map((opt) => {
            const active = gender === opt.value;
            return (
              <Pressable
                key={opt.value}
                style={[styles.pill, active && styles.pillActive]}
                onPress={() => setGender(active ? "" : opt.value)}
              >
                {active && <LinearGradient colors={grad.subtle} style={StyleSheet.absoluteFill} borderRadius={10} />}
                <Text style={[styles.pillText, active && styles.pillTextActive]}>{opt.label}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* ── Date of Birth ── */}
        <View>
          <Text style={styles.label}>
            Date of Birth
            {age !== null ? (
              <Text style={[styles.labelHint, isMinor && styles.labelHintWarn]}>
                {"   "}Age {age}{isMinor ? " — parent mobile required" : ""}
              </Text>
            ) : null}
          </Text>

          <Pressable style={styles.dateBtn} onPress={() => {
            setTempDate(dob || new Date(2005, 0, 1));
            setShowDatePicker(true);
          }}>
            <Ionicons name="calendar-outline" size={18} color={dob ? colors.gradStart : colors.textDim} />
            <Text style={[styles.dateBtnText, !dob && styles.dateBtnPlaceholder]}>
              {dob ? formatDisplayDate(dob) : "Select date of birth"}
            </Text>
            {dob && (
              <Pressable hitSlop={8} onPress={() => setDob(null)}>
                <Ionicons name="close-circle" size={16} color={colors.textDim} />
              </Pressable>
            )}
          </Pressable>

          {/* Android — native calendar dialog */}
          {Platform.OS === "android" && showDatePicker && (
            <DateTimePicker
              value={tempDate || new Date(2005, 0, 1)}
              mode="date"
              display="calendar"
              maximumDate={new Date()}
              minimumDate={new Date(1920, 0, 1)}
              onChange={(e, selected) => {
                setShowDatePicker(false);
                if (e.type !== "dismissed" && selected) setDob(selected);
              }}
            />
          )}

          {/* iOS — spinner in a modal sheet */}
          {Platform.OS === "ios" && (
            <Modal
              visible={showDatePicker}
              transparent
              animationType="slide"
              onRequestClose={() => setShowDatePicker(false)}
            >
              <Pressable style={styles.modalOverlay} onPress={() => setShowDatePicker(false)} />
              <View style={styles.pickerSheet}>
                <View style={styles.pickerSheetHeader}>
                  <Pressable onPress={() => setShowDatePicker(false)}>
                    <Text style={styles.pickerCancel}>Cancel</Text>
                  </Pressable>
                  <Pressable onPress={() => { setDob(tempDate); setShowDatePicker(false); }}>
                    <Text style={styles.pickerDone}>Done</Text>
                  </Pressable>
                </View>
                <DateTimePicker
                  value={tempDate || new Date(2005, 0, 1)}
                  mode="date"
                  display="spinner"
                  maximumDate={new Date()}
                  minimumDate={new Date(1920, 0, 1)}
                  themeVariant="dark"
                  onChange={(_, selected) => { if (selected) setTempDate(selected); }}
                  style={styles.iosPicker}
                />
              </View>
            </Modal>
          )}

          {errors.date_of_birth ? (
            <Text style={styles.fieldError}>
              {Array.isArray(errors.date_of_birth) ? errors.date_of_birth[0] : errors.date_of_birth}
            </Text>
          ) : null}
        </View>

        {/* ── Parent mobile — only when under 18 ── */}
        {isMinor && (
          <Field
            label="Parent / Guardian Mobile"
            required
            value={parentMobile}
            onChange={setParentMobile}
            keyboardType="phone-pad"
            placeholder="+91 9XXXXXXXXX"
            error={errors.parent_mobile}
          />
        )}

        {/* ── Location ── */}
        <View>
          <Text style={styles.label}>Pincode</Text>
          <View style={styles.pincodeRow}>
            <TextInput
              style={[styles.input, styles.pincodeInput]}
              value={pincode}
              onChangeText={(v) => setPincode(v.replace(/\D/g, "").slice(0, 6))}
              keyboardType="numeric"
              placeholder="6-digit pincode"
              placeholderTextColor={colors.textDim}
              maxLength={6}
            />
            {pincodeStatus === "loading" && (
              <ActivityIndicator color={colors.gradStart} size="small" style={styles.pincodeSpinner} />
            )}
            {pincodeStatus === "notfound" && (
              <Text style={styles.pincodeNotFound}>Not found</Text>
            )}
          </View>
        </View>

        {(city || state) ? (
          <View style={styles.locationRow}>
            <View style={styles.locationChip}>
              <Text style={styles.locationLabel}>City</Text>
              <TextInput
                style={styles.locationInput}
                value={city}
                onChangeText={setCity}
                placeholderTextColor={colors.textDim}
                placeholder="City"
              />
            </View>
            <View style={styles.locationChip}>
              <Text style={styles.locationLabel}>State</Text>
              <TextInput
                style={styles.locationInput}
                value={state}
                onChangeText={setState}
                placeholderTextColor={colors.textDim}
                placeholder="State"
              />
            </View>
          </View>
        ) : null}

        {/* ── Athlete / Academy extras ── */}
        {hasAthlete && (
          <Field label="Sport" value={sport} onChange={setSport} error={errors.athlete_sport} />
        )}
        {hasAcademy && (
          <>
            <Field label="Academy Name" value={academyName} onChange={setAcademyName} error={errors.academy_name} />
            <Field label="Academy City" value={academyCity} onChange={setAcademyCity} error={errors.academy_city} />
          </>
        )}

        {/* ── Message ── */}
        <Text style={styles.label}>Message <Text style={styles.labelHint}>optional</Text></Text>
        <TextInput
          style={[styles.input, { height: 96, textAlignVertical: "top" }]}
          value={message}
          onChangeText={setMessage}
          multiline
          placeholderTextColor={colors.textDim}
          placeholder="Anything else you'd like us to know…"
        />

        <Pressable style={[styles.btnWrap, loading && { opacity: 0.6 }]} onPress={handleSubmit} disabled={loading}>
          <LinearGradient colors={grad.accent} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.btn}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Submit Enquiry</Text>}
          </LinearGradient>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── Field component ──────────────────────────────────────────────────────────

function Field({ label, required, value, onChange, keyboardType, error, placeholder }) {
  return (
    <View>
      <Text style={styles.label}>
        {label}
        {required ? <Text style={styles.required}> *</Text> : null}
      </Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        keyboardType={keyboardType}
        autoCapitalize="none"
        autoCorrect={false}
        placeholderTextColor={colors.textDim}
        placeholder={placeholder}
      />
      {error ? <Text style={styles.fieldError}>{Array.isArray(error) ? error[0] : error}</Text> : null}
    </View>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  content: { padding: 20, paddingBottom: 60 },
  pageTitle: { fontSize: font["2xl"], fontWeight: "800", color: colors.white, marginBottom: 6 },
  pageSubtitle: { fontSize: font.sm, color: colors.textMuted, marginBottom: 28 },
  label: { fontSize: font.sm, color: colors.textMuted, marginBottom: 8, marginTop: 16 },
  labelHint: { fontSize: font.xs, color: colors.textDim },
  labelHintWarn: { color: "#f87171" },
  required: { color: colors.gradStart },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: colors.white,
    fontSize: font.base,
  },
  // Multi-select type chips
  typeGrid: { gap: 8 },
  typeChip: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 14,
    overflow: "hidden",
  },
  typeChipActive: { borderColor: colors.gradStart + "88" },
  typeChipRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: colors.border,
    justifyContent: "center",
    alignItems: "center",
  },
  checkboxActive: { borderColor: colors.gradStart, backgroundColor: colors.gradStart + "22" },
  checkmark: { fontSize: 11, color: colors.gradStart, fontWeight: "700" },
  typeChipText: { color: colors.textMuted, fontSize: font.sm, flex: 1 },
  typeChipTextActive: { color: colors.gradStart, fontWeight: "600" },
  // Gender / pill row
  pillRow: { flexDirection: "row", gap: 8 },
  pill: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 18,
    overflow: "hidden",
  },
  pillActive: { borderColor: colors.gradStart + "88" },
  pillText: { color: colors.textMuted, fontSize: font.sm },
  pillTextActive: { color: colors.gradStart, fontWeight: "600" },
  // Date picker button
  dateBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  dateBtnText: { flex: 1, color: colors.white, fontSize: font.base },
  dateBtnPlaceholder: { color: colors.textDim },
  // iOS modal sheet
  modalOverlay: { flex: 1, backgroundColor: "#00000066" },
  pickerSheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 32,
    borderTopWidth: 1,
    borderColor: colors.border,
  },
  pickerSheetHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderColor: colors.border,
  },
  pickerCancel: { fontSize: font.base, color: colors.textMuted },
  pickerDone: { fontSize: font.base, color: colors.gradStart, fontWeight: "700" },
  iosPicker: { backgroundColor: colors.surface },
  // Pincode
  pincodeRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  pincodeInput: { flex: 1 },
  pincodeSpinner: { marginLeft: 4 },
  pincodeNotFound: { fontSize: font.xs, color: "#f87171" },
  // Location chips
  locationRow: { flexDirection: "row", gap: 10, marginTop: 10 },
  locationChip: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.gradStart + "44",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  locationLabel: { fontSize: font.xs, color: colors.gradStart, marginBottom: 2 },
  locationInput: { color: colors.white, fontSize: font.sm, padding: 0 },
  // Button
  btnWrap: { marginTop: 28 },
  btn: { borderRadius: 12, paddingVertical: 16, alignItems: "center" },
  btnText: { fontSize: font.base, fontWeight: "700", color: "#fff" },
  // Errors
  fieldError: { color: "#f87171", fontSize: font.xs, marginTop: 4 },
  errorBanner: {
    color: "#f87171",
    fontSize: font.sm,
    backgroundColor: "#2a0a0a",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#7f1d1d",
  },
  // Success
  successRoot: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
    overflow: "hidden",
  },
  successIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 20,
  },
  successIcon: { fontSize: 30, color: "#fff" },
  successTitle: { fontSize: font.xl, fontWeight: "800", color: colors.white, marginBottom: 10 },
  successBody: { fontSize: font.sm, color: colors.textMuted, textAlign: "center", lineHeight: 22, marginBottom: 32 },
});
