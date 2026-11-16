module.exports = {
  expo: {
    name: "AlphaMinds",
    slug: "AlphamindsApp",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "dark",
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#0c0d11",
    },
    ios: {
      supportsTablet: true,
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#0c0d11",
      },
    },
    web: {
      favicon: "./assets/favicon.png",
    },
    plugins: ["@react-native-community/datetimepicker"],
    extra: {
      apiUrl: process.env.EXPO_PUBLIC_API_URL,
    },
  },
};
