module.exports = {
  preset: "jest-expo",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testMatch: ["<rootDir>/src/App.test.tsx"],
  transformIgnorePatterns: [
    "node_modules/(?!(react-native|@react-native|expo|expo-.*|@expo|@expo/.*|expo-modules-core|expo-image-picker|convex)/)",
  ],
};
