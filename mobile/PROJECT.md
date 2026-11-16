# AlphaMinds App: Project Overview

> Purpose of this document: give an LLM (or a new developer) enough context to analyse, review or extend this codebase. It describes the mobile client only. The backend is a separate project and is summarised only through the API contract the app consumes.

## 1. What it is

**AlphaMinds** is a dark-themed, portrait-only mobile app (Expo / React Native) for **athletes** enrolled in a sports mental-performance and cognitive assessment programme (mental toughness, cognitive vision, emotional regulation). Athletes can:

- Log in and recover a forgotten password.
- View a dashboard with their primary enrollment and recent assessments.
- Browse published assessment sessions and open the metric-level detail.
- View their profile and enrollment information.
- Submit a public "Get in Touch" lead enquiry (also reachable before login, from the Login screen's sign-up link).

The app is **athlete-facing only**. There are no coach, admin or staff features in this codebase.

## 2. Tech stack

| Area | Choice |
|---|---|
| Framework | Expo SDK ~54, React Native 0.81.5, React 19.1 |
| Language | Plain JavaScript (no TypeScript) |
| Navigation | `@react-navigation/native` v7, native-stack, bottom-tabs |
| HTTP | axios ^1.15 (plus one raw `fetch` for pincode lookup) |
| Storage | `@react-native-async-storage/async-storage` (JWT tokens) |
| UI extras | `expo-linear-gradient`, `@expo/vector-icons`, `@react-native-community/datetimepicker` |
| State | React local state plus a single `AuthContext`. No Redux or other store. |
| Tests / lint / types | None configured |

Scripts: `npm start`, `npm run android`, `npm run ios`, `npm run web` (all `expo start ...`).

## 3. Repository layout

```
AlphamindsApp/
├── App.js                      # SafeAreaProvider > AuthProvider > AppNavigator
├── index.js                    # registerRootComponent(App)
├── app.json                    # Expo config (name AlphaMinds, dark UI, portrait)
├── assets/                     # icon, adaptive-icon, splash-icon, favicon
└── src/
    ├── api/
    │   ├── client.js           # axios instance, auth header, 401 refresh interceptor, BASE_URL
    │   ├── auth.js             # login, logout, forgotPassword, getStoredTokens
    │   ├── athlete.js          # getMe, getDashboard, getSessions, getSessionDetail
    │   └── leads.js            # submitLead
    ├── contexts/AuthContext.js # user, loading, login(), logout(); session restore
    ├── navigation/AppNavigator.js
    ├── components/GradientCard.js
    ├── screens/
    │   ├── LoginScreen.js            (~230 lines)
    │   ├── ForgotPasswordScreen.js   (~165)
    │   ├── DashboardScreen.js        (~200)
    │   ├── SessionListScreen.js      (~130)
    │   ├── SessionDetailScreen.js    (~215)
    │   ├── LeadInquiryScreen.js      (~635, largest)
    │   └── ProfileScreen.js          (~385)
    └── theme.js                # colors, font scale, gradient presets
```

## 4. Architecture

### 4.1 Entry and providers
`App.js` renders `SafeAreaProvider`, then `AuthProvider`, then `AppNavigator`.

### 4.2 Auth flow
- `AuthContext` holds `user` and `loading`.
- On mount it reads `access_token` from AsyncStorage. If a token exists it sets `user = { restored: true }`. It does not fetch the profile. After a restore, `user.full_name` and `user.athlete_id` are absent until some screen loads data. Screens fall back to `data.athlete.full_name`.
- `login(username, password)` POSTs to `/auth/login/` and stores `access` and `refresh` in AsyncStorage. It sets `user = { athlete_id, full_name }` from the response.
- `logout()` POSTs the refresh token to `/auth/logout/` (best effort), clears both tokens, and sets `user = null`.
- `AppNavigator` renders `user ? <AppStack/> : <AuthStack/>`, with a spinner while `loading` is true.

### 4.3 Navigation tree
```
NavigationContainer (custom dark theme)
├─ AuthStack (user == null; headers hidden)
│   ├─ Login
│   ├─ ForgotPassword
│   └─ SignUp  -> LeadInquiryScreen with params { athleteOnly: true }  (header shown, title "Get in Touch")
└─ AppStack (user != null)
    ├─ Main -> AppTabs (bottom tabs)
    │     ├─ Dashboard            DashboardScreen
    │     ├─ Sessions             SessionListScreen   (title "Assessments")
    │     ├─ Enquire              LeadInquiryScreen   (title "Get in Touch")
    │     └─ Profile              ProfileScreen       (title "My Profile")
    └─ SessionDetail              SessionDetailScreen (title "Assessment Detail", param: session_id)
```
Tab icons are unicode glyphs (a placeholder noted in a code comment). `@expo/vector-icons` is used on the Profile screen.

### 4.4 Networking ([src/api/client.js](src/api/client.js))
- `BASE_URL = process.env.EXPO_PUBLIC_API_URL` (set in `mobile/.env`; see `.env.example`).
- Request interceptor attaches `Authorization: Bearer <access_token>`.
- Response interceptor: on a 401 (once per request, using an `_retry` flag) it POSTs `{refresh}` to `/auth/refresh/`, stores the new access token, and retries. If the refresh fails it clears the tokens and rejects the error. It does **not** update `AuthContext`, so the UI stays on the logged-in stack until the next navigation or restart.
- Timeout is 15 s. `auth.js` uses bare `axios` instead of the `client` instance, so the interceptors don't apply to login, logout, forgot-password or the refresh call.

## 5. Backend API contract (as consumed by the app)

Base: `/api/v1`. The server looks like Django REST with JWT (SimpleJWT-style `access`/`refresh`).

| Method | Path | Auth | Used by | Notes |
|---|---|---|---|---|
| POST | `/auth/login/` | no | LoginScreen | body `{username, password}` returns `{access, refresh, athlete_id, full_name}` |
| POST | `/auth/logout/` | Bearer | AuthContext | body `{refresh}` |
| POST | `/auth/refresh/` | no | client interceptor | body `{refresh}` returns `{access}` |
| POST | `/auth/forgot-password/` | no | ForgotPasswordScreen | body `{email}` |
| GET | `/athlete/me/` | yes | defined in `athlete.js`, **not used by any screen** | |
| GET | `/athlete/dashboard/` | yes | Dashboard **and** Profile | returns `{athlete, primary_enrollment, recent_sessions[]}` |
| GET | `/athlete/sessions/` | yes | SessionListScreen | list of sessions |
| GET | `/athlete/sessions/{id}/` | yes | SessionDetailScreen | session with `metric_values[]` |
| POST | `/leads/` | no (but sent with a token if present) | LeadInquiryScreen | see below |

### Response shapes inferred from the UI code
- `athlete`: `full_name`, `date_of_birth`, `gender_display`, `dominant_hand`, `email`, `phone`
- `primary_enrollment`: `sport_name`, `center_name`, `batch_name`, `status`, `start_date`, `end_date`
- `session`: `id`, `domain_name`, `protocol_name`, `framework_name`, `sport_name`, `assessed_on`, `status` (`"published"` etc.), `notes`, `metric_values[]`
- `metric_value`: `id`, `metric_label` or `metric_name`, `display_value`, `units`

### Lead payload (`POST /leads/`)
`inquiry_types[]`, `full_name`, `email`, `mobile_number`, `gender` (`M`/`F`/`O`), `date_of_birth` (ISO, nullable), `parent_mobile`, `pincode`, `city`, `state`, `athlete_sport`, `academy_name`, `academy_city`, `message`.

Inquiry type values: `athlete_mental_toughness`, `athlete_cognitive_vision`, `athlete_emotional_regulation`, `academy_partnership`. When `athleteOnly` is true (the pre-login route) the academy option is hidden.

## 6. Screens

- **Login**: username and password, show/hide password, error display, links to Forgot Password and "SignUp" (the lead form).
- **ForgotPassword**: email field, shows a submitted/confirmation state.
- **Dashboard**: pull-to-refresh. A hero card shows the athlete name and the sport and centre pill. "Recent Assessments" lists cards (domain, status badge, protocol, framework, date in `en-IN`). Tapping a card opens SessionDetail.
- **SessionList**: pull-to-refresh list of all sessions, each opening SessionDetail.
- **SessionDetail**: header (domain, protocol, framework), meta chips (sport, date, status), notes, and a list of metric rows. A published-only gate exists (`isPublished`).
- **Profile**: calls `getDashboard()` (not `getMe()`). Shows personal info (DOB with age, gender, dominant hand, email, phone) and enrollment (sport, centre, batch, status badge, start and end dates). Has a logout action.
- **LeadInquiry**: multi-select interest chips, personal details, a DOB picker (iOS staging value), a parent mobile number required when the age is under 18, and a 6-digit India **pincode lookup** (`https://api.postalpincode.in/pincode/{pin}` via `fetch`, which fills city and state). It also takes athlete sport and academy fields (shown conditionally), a message, client-side validation, server error mapping (`e.response.data`), and a success state with reset.

## 7. Design system ([src/theme.js](src/theme.js))
- Dark only (`userInterfaceStyle: "dark"`). Background `#0c0d11`, surface `#13141c`, border `#1e2030`.
- Signature accent gradient cyan `#06c8d4` to indigo `#6366f1` to violet `#8b2fc9`. `grad.accent`, `grad.accentH` and `grad.subtle` are presets.
- Text colours: `white`, `textMuted #8a8b9e`, `textDim #4a4b5e`. Status colours: green, red, yellow.
- The font scale runs from `xs` (11) to `3xl` (34). Legacy aliases (`black`, `card`, `zinc*`) are kept for older code.
- `GradientCard` is the main reusable component: a surface card with a gradient bar at the bottom.

## 8. Known issues and risks (for the reviewer)

1. **Hardcoded `BASE_URL`** (a private LAN IP over plain HTTP). There is no env or config switch, so it can't ship as is, and cleartext HTTP needs extra Android and iOS config.
2. **Tokens are stored in AsyncStorage**, which is unencrypted. `expo-secure-store` would be more appropriate.
3. **Session restore is shallow.** `{restored: true}` means there is no athlete info until a screen fetches it. There is no token validation at startup.
4. **A failed refresh doesn't log the user out in the UI.** The interceptor clears the tokens, but `AuthContext.user` is never reset.
5. **Auth calls bypass the shared axios client** (`auth.js` uses raw `axios`), so there are duplicate header and timeout concerns and no shared error handling.
6. **Duplicate fetching.** Dashboard and Profile both call `getDashboard()`, and `getMe()` is unused. There is no caching or shared data layer. `calcAge` is duplicated in `LeadInquiryScreen` and `ProfileScreen`.
7. **Lead form details:** the pincode lookup calls a third-party API with no timeout, and failures are silently swallowed. Validation is minimal (no email or phone format checks). The `athleteOnly` param exists on the pre-login route but the in-app "Enquire" tab shows all four options.
8. **Navigation naming:** the pre-login route is called `SignUp` but renders a lead enquiry form, not an account registration.
9. **No tests, lint, TypeScript or error boundary.** Error handling is mostly a generic string per screen.
10. **Accessibility and i18n:** no accessibility labels were seen, dates are hardcoded to `en-IN`, and the strings aren't localised.
11. **Repo state:** `src/` and the workspace file are untracked, and only the "Initial commit" exists. The branch is `master` while the main branch is `main`. The `NeuroGym.code-workspace` name suggests an earlier or alternate project name.

## 9. Suggested analysis prompts

- "Review the auth and token-refresh flow for race conditions (parallel 401s) and logout-sync bugs."
- "Propose a data layer (e.g. React Query) to remove duplicate dashboard fetching and add caching and retry."
- "Audit LeadInquiryScreen for validation gaps, accessibility, and how it could be split into smaller components."
- "Suggest an environment-config strategy (app.config.js + EXPO_PUBLIC_* vars) and secure token storage."
- "Check the API contract above against the backend serializers and flag mismatches."

## 10. Running locally

```bash
npm install
# set BASE_URL in src/api/client.js to a host reachable from the device or emulator
npm start        # then press a / i / w, or scan the QR code in Expo Go
```
The backend must be reachable at `BASE_URL` (the value of `EXPO_PUBLIC_API_URL`, e.g. `http://<your-pc-ip>:8000/api/v1`).
