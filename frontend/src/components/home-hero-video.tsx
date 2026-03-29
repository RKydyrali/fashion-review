import { Platform } from "react-native";

import type { ComponentType } from "react";

type HomeHeroVideoProps = {
  height: number;
};

const HomeHeroVideoImpl = (
  Platform.OS === "web"
    ? require("./home-hero-video.web")
    : require("./home-hero-video.native")
).HomeHeroVideo as ComponentType<HomeHeroVideoProps>;

export function HomeHeroVideo(props: HomeHeroVideoProps) {
  return <HomeHeroVideoImpl {...props} />;
}
