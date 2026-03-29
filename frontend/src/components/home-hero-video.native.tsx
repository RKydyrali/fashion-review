import { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import { VideoView, useVideoPlayer } from "expo-video";

import { editorialSerif } from "@/components/ui";

const welcomeVideo = require("../../welcome.mov");

export function HomeHeroVideo({ height }: { height: number }) {
  const player = useVideoPlayer(welcomeVideo);

  useEffect(() => {
    player.loop = true;
    player.muted = true;
    player.play();

    return () => {
      player.pause();
    };
  }, [player]);

  return (
    <View style={[styles.shell, { height }]}>
      <VideoView
        player={player}
        style={styles.video}
        contentFit="cover"
        nativeControls={false}
        allowsFullscreen={false}
        allowsPictureInPicture={false}
      />
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
    width: "100%",
    height: "100%"
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
