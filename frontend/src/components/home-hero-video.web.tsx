import { StyleSheet, Text, View } from "react-native";

import { editorialSerif, editorialTheme } from "@/components/ui";

const welcomeVideo = require("../../welcome.mov");

const videoSrc =
  typeof welcomeVideo === "string"
    ? welcomeVideo
    : typeof welcomeVideo?.uri === "string"
      ? welcomeVideo.uri
      : typeof welcomeVideo?.default === "string"
        ? welcomeVideo.default
        : "";

export function HomeHeroVideo({ height }: { height: number }) {
  return (
    <View style={[styles.shell, { height }]}>
      {videoSrc ? <video autoPlay muted loop playsInline style={styles.video} src={videoSrc} /> : null}
      <View style={styles.overlay} />
      <View style={styles.copyWrap}>
        <Text style={styles.copy}>AVISHU</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: {
    position: "relative",
    width: "100%",
    overflow: "hidden",
    backgroundColor: "#000000"
  },
  video: {
    position: "absolute",
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    backgroundColor: "#000000"
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0, 0, 0, 0.22)"
  },
  copyWrap: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none"
  },
  copy: {
    fontFamily: editorialSerif,
    fontSize: 40,
    lineHeight: 48,
    letterSpacing: 8,
    textTransform: "uppercase",
    color: "#FFFFFF",
    textShadowColor: "rgba(0, 0, 0, 0.45)",
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 12
  }
});
