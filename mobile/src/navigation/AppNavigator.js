import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { ActivityIndicator, Text, View } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import { useAuth } from "../contexts/AuthContext";
import { colors, font, grad } from "../theme";

import LoginScreen from "../screens/LoginScreen";
import ForgotPasswordScreen from "../screens/ForgotPasswordScreen";
import DashboardScreen from "../screens/DashboardScreen";
import SessionListScreen from "../screens/SessionListScreen";
import SessionDetailScreen from "../screens/SessionDetailScreen";
import LeadInquiryScreen from "../screens/LeadInquiryScreen";
import ProfileScreen from "../screens/ProfileScreen";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const headerOptions = {
  headerStyle: { backgroundColor: colors.bg },
  headerTintColor: colors.white,
  headerTitleStyle: { fontWeight: "700", fontSize: font.base },
  headerShadowVisible: false,
};

// Tab icons (unicode — swap for react-native-vector-icons / expo-symbols later)
const TAB_ICONS = {
  Dashboard: { active: "◉", inactive: "○" },
  Sessions: { active: "▤", inactive: "▤" },
  Enquire: { active: "✉", inactive: "✉" },
  Profile: { active: "◈", inactive: "◇" },
};

function TabIcon({ name, focused }) {
  const icon = TAB_ICONS[name];
  return (
    <View>
      <Text style={{ fontSize: 18, color: focused ? colors.gradStart : colors.textDim }}>
        {focused ? icon?.active : icon?.inactive}
      </Text>
      {focused && (
        <LinearGradient
          colors={grad.accentH}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={{
            height: 2,
            borderRadius: 1,
            marginTop: 3,
            width: "100%",
          }}
        />
      )}
    </View>
  );
}

function AppTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        ...headerOptions,
        tabBarStyle: {
          backgroundColor: colors.bg,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingBottom: 6,
          height: 60,
        },
        tabBarActiveTintColor: colors.gradStart,
        tabBarInactiveTintColor: colors.textDim,
        tabBarLabelStyle: { fontSize: font.xs, marginBottom: 2 },
        tabBarIcon: ({ focused }) => <TabIcon name={route.name} focused={focused} />,
        tabBarLabel: ({ focused, color }) => (
          <Text style={{ fontSize: font.xs, color, marginBottom: 2 }}>
            {route.name}
          </Text>
        ),
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ ...headerOptions }} />
      <Tab.Screen
        name="Sessions"
        component={SessionListScreen}
        options={{ ...headerOptions, title: "Assessments" }}
      />
      <Tab.Screen
        name="Enquire"
        component={LeadInquiryScreen}
        options={{ ...headerOptions, title: "Get in Touch" }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ ...headerOptions, title: "My Profile" }}
      />
    </Tab.Navigator>
  );
}

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
      <Stack.Screen
        name="SignUp"
        component={LeadInquiryScreen}
        initialParams={{ athleteOnly: true }}
        options={{ headerShown: true, ...headerOptions, title: "Get in Touch" }}
      />
    </Stack.Navigator>
  );
}

function AppStack() {
  return (
    <Stack.Navigator screenOptions={headerOptions}>
      <Stack.Screen name="Main" component={AppTabs} options={{ headerShown: false }} />
      <Stack.Screen
        name="SessionDetail"
        component={SessionDetailScreen}
        options={{ title: "Assessment Detail" }}
      />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator color={colors.gradStart} size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer
      theme={{
        dark: true,
        colors: {
          primary: colors.gradStart,
          background: colors.bg,
          card: colors.bg,
          text: colors.white,
          border: colors.border,
          notification: colors.gradStart,
        },
        fonts: {
          regular: { fontFamily: "System", fontWeight: "400" },
          medium: { fontFamily: "System", fontWeight: "500" },
          bold: { fontFamily: "System", fontWeight: "700" },
          heavy: { fontFamily: "System", fontWeight: "900" },
        },
      }}
    >
      {user ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  );
}
