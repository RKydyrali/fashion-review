import { VideoView, useVideoPlayer } from "expo-video";
import { StyleSheet } from "react-native";

const welcomeVideo = require("../../welcome.mov");

export function WelcomeBackground() {
  const player = useVideoPlayer(welcomeVideo, (videoPlayer) => {
    videoPlayer.loop = true;
    videoPlayer.muted = true;
    videoPlayer.play();
  });

  return (
    <VideoView
      player={player}
      style={StyleSheet.absoluteFill}
      contentFit="cover"
      nativeControls={false}
      allowsFullscreen={false}
      allowsPictureInPicture={false}
    />
  );
}
