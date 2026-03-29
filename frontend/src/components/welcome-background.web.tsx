import { StyleSheet, View } from "react-native";

const welcomeVideo = require("../../welcome.mov");

const videoSrc =
  typeof welcomeVideo === "string"
    ? welcomeVideo
    : typeof welcomeVideo?.uri === "string"
      ? welcomeVideo.uri
      : typeof welcomeVideo?.default === "string"
        ? welcomeVideo.default
        : "";

export function WelcomeBackground() {
  return (
    <View style={styles.container}>
      {videoSrc ? (
        <video
          autoPlay
          muted
          loop
          playsInline
          style={styles.video}
          src={videoSrc}
        />
      ) : null}
      <View style={styles.base} />
      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    overflow: "hidden",
    backgroundColor: "#09090B"
  },
  base: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    backgroundColor: "rgba(9, 9, 11, 0.24)"
  },
  video: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundColor: "#09090B",
    objectFit: "cover"
  },
  glowTop: {
    position: "absolute",
    top: -120,
    left: -40,
    right: -40,
    height: 320,
    borderRadius: 320,
    backgroundColor: "rgba(255, 255, 255, 0.07)"
  },
  glowBottom: {
    position: "absolute",
    bottom: -140,
    left: 30,
    right: 30,
    height: 260,
    borderRadius: 260,
    backgroundColor: "rgba(255, 255, 255, 0.05)"
  }
});
