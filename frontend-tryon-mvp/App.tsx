import "react-native-get-random-values";
import "react-native-url-polyfill/auto";

import { ConvexProvider, ConvexReactClient } from "convex/react";
import { StatusBar } from "expo-status-bar";

import { FashionTryOnScreen } from "./src/FashionTryOnScreen";

const convexUrl = process.env.EXPO_PUBLIC_CONVEX_URL;
const convexClient = convexUrl ? new ConvexReactClient(convexUrl) : null;

export default function App() {
  if (!convexUrl) {
    return <FashionTryOnScreen missingConfig="EXPO_PUBLIC_CONVEX_URL" />;
  }

  return (
    <ConvexProvider client={convexClient!}>
      <FashionTryOnScreen />
      <StatusBar style="auto" />
    </ConvexProvider>
  );
}
