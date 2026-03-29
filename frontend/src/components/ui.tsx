import { Image } from "expo-image";
import { PropsWithChildren } from "react";
import { ImageStyle, Pressable, ScrollView, StyleProp, StyleSheet, Text, TextStyle, View, ViewStyle } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export const editorialTheme = {
  background: "#FFFFFF",
  surface: "#FFFFFF",
  surfaceMuted: "#F5F5F5",
  surfaceStrong: "#E9E9E9",
  border: "#D6D6D6",
  borderStrong: "#9C9C9C",
  text: "#000000",
  textMuted: "#4F4F4F",
  textSoft: "#7A7A7A",
  shadow: "#000000",
  empty: "#EFEFEF",
  success: "#2F2F2F",
  danger: "#1A1A1A"
} as const;

export const editorialSerif = "SpaceGrotesk_700Bold";

type ScreenProps = PropsWithChildren<{
  contentContainerStyle?: StyleProp<ViewStyle>;
}>;

type TextProps = PropsWithChildren<{
  style?: StyleProp<TextStyle>;
}>;

type ViewProps = PropsWithChildren<{
  style?: StyleProp<ViewStyle>;
}>;

export function Screen({ children, contentContainerStyle }: ScreenProps) {
  return (
    <SafeAreaView style={styles.safeArea} edges={["top"]}>
      <ScrollView
        style={styles.screen}
        contentContainerStyle={[styles.screenContent, contentContainerStyle]}
        showsVerticalScrollIndicator={false}
      >
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export function SectionLabel({ children, style }: TextProps) {
  return <Text style={[styles.sectionLabel, style]}>{children}</Text>;
}

export function EditorialTitle({ children, style }: TextProps) {
  return <Text style={[styles.editorialTitle, style]}>{children}</Text>;
}

export function BodyText({ children, style }: TextProps) {
  return <Text style={[styles.bodyText, style]}>{children}</Text>;
}

export function Divider() {
  return <View style={styles.divider} />;
}

export function EditorialButton({
  label,
  onPress,
  inverse,
  disabled,
  style,
  textStyle
}: {
  label: string;
  onPress?: () => void;
  inverse?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.buttonBase,
        inverse ? styles.buttonInverse : styles.buttonPrimary,
        pressed && !disabled ? styles.buttonPressed : null,
        disabled ? styles.buttonDisabled : null,
        style
      ]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={[styles.buttonText, inverse ? styles.buttonTextInverse : styles.buttonTextPrimary, textStyle]}>{label}</Text>
    </Pressable>
  );
}

export function CardFrame({ children, style }: ViewProps) {
  return <View style={[styles.cardFrame, style]}>{children}</View>;
}

export function SoftPanel({ children, style }: ViewProps) {
  return <View style={[styles.softPanel, style]}>{children}</View>;
}

export function EditorialPill({
  label,
  strong,
  style,
  textStyle
}: {
  label: string;
  strong?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}) {
  return (
    <View style={[styles.pillBase, strong ? styles.pillStrong : styles.pillMuted, style]}>
      <Text style={[styles.pillText, strong ? styles.pillTextStrong : null, textStyle]}>{label}</Text>
    </View>
  );
}

export function MetricTile({ label, value, style }: { label: string; value: string; style?: StyleProp<ViewStyle> }) {
  return (
    <View style={[styles.metricTile, style]}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

export function SkeletonBlock({ height = 24, style }: { height?: number; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.skeletonBlock, { height }, style]} />;
}

export function ProductImage({
  uri,
  height = 360,
  style
}: {
  uri?: string | null;
  height?: number;
  style?: StyleProp<ImageStyle>;
}) {
  return <Image source={uri ? { uri } : undefined} style={[styles.productImage, { height }, style]} contentFit="cover" />;
}

export function InlineNotice({ title, description, style }: { title: string; description: string; style?: StyleProp<ViewStyle> }) {
  return (
    <View style={[styles.noticeCard, style]}>
      <Text style={styles.noticeTitle}>{title}</Text>
      <Text style={styles.noticeBody}>{description}</Text>
    </View>
  );
}

export function QuantityStepper({
  value,
  onChange,
  min = 1,
  max = 10,
  style
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.stepperShell, style]}>
      <Pressable
        style={({ pressed }) => [styles.stepperButton, pressed && value > min ? styles.buttonPressed : null, value <= min ? styles.stepperButtonDisabled : null]}
        onPress={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
      >
        <Text style={[styles.stepperButtonText, value <= min ? styles.stepperButtonTextDisabled : null]}>-</Text>
      </Pressable>
      <View style={styles.stepperValueWrap}>
        <Text style={styles.stepperValue}>{value}</Text>
      </View>
      <Pressable
        style={({ pressed }) => [styles.stepperButton, pressed && value < max ? styles.buttonPressed : null, value >= max ? styles.stepperButtonDisabled : null]}
        onPress={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
      >
        <Text style={[styles.stepperButtonText, value >= max ? styles.stepperButtonTextDisabled : null]}>+</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  screen: {
    flex: 1,
    backgroundColor: editorialTheme.background
  },
  screenContent: {
    paddingHorizontal: 28,
    paddingTop: 22,
    paddingBottom: 162
  },
  sectionLabel: {
    marginBottom: 8,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 3,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  editorialTitle: {
    fontFamily: editorialSerif,
    fontSize: 38,
    lineHeight: 46,
    letterSpacing: 2.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  bodyText: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 16,
    lineHeight: 30,
    color: editorialTheme.textMuted
  },
  divider: {
    height: 1,
    marginVertical: 24,
    backgroundColor: editorialTheme.border
  },
  buttonBase: {
    minHeight: 56,
    borderRadius: 3,
    paddingHorizontal: 24,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1
  },
  buttonPrimary: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  buttonInverse: {
    backgroundColor: editorialTheme.surface,
    borderColor: editorialTheme.borderStrong
  },
  buttonPressed: {
    opacity: 0.84
  },
  buttonDisabled: {
    opacity: 0.55
  },
  buttonText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 16,
    letterSpacing: 1.8,
    textTransform: "uppercase"
  },
  buttonTextPrimary: {
    color: editorialTheme.surface
  },
  buttonTextInverse: {
    color: editorialTheme.text
  },
  cardFrame: {
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    padding: 20
  },
  softPanel: {
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    padding: 20
  },
  pillBase: {
    minHeight: 34,
    borderRadius: 2,
    paddingHorizontal: 14,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1
  },
  pillMuted: {
    backgroundColor: editorialTheme.surface,
    borderColor: editorialTheme.border
  },
  pillStrong: {
    backgroundColor: editorialTheme.surfaceStrong,
    borderColor: editorialTheme.borderStrong
  },
  pillText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.textMuted
  },
  pillTextStrong: {
    color: editorialTheme.text
  },
  metricTile: {
    flex: 1,
    minHeight: 96,
    borderRadius: 2,
    backgroundColor: editorialTheme.surface,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    paddingHorizontal: 16,
    paddingVertical: 14,
    justifyContent: "space-between"
  },
  metricLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  metricValue: {
    fontFamily: editorialSerif,
    fontSize: 24,
    lineHeight: 28,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  skeletonBlock: {
    marginBottom: 14,
    borderRadius: 2,
    backgroundColor: editorialTheme.empty
  },
  productImage: {
    width: "100%",
    borderRadius: 2,
    backgroundColor: editorialTheme.empty
  },
  noticeCard: {
    borderRadius: 2,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    padding: 20
  },
  noticeTitle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  noticeBody: {
    marginTop: 10,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    lineHeight: 24,
    color: editorialTheme.textMuted
  },
  stepperShell: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    borderRadius: 2,
    overflow: "hidden"
  },
  stepperButton: {
    width: 46,
    alignSelf: "stretch",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: editorialTheme.surface
  },
  stepperButtonDisabled: {
    backgroundColor: editorialTheme.surfaceMuted
  },
  stepperButtonText: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 24,
    color: editorialTheme.text
  },
  stepperButtonTextDisabled: {
    color: editorialTheme.textSoft
  },
  stepperValueWrap: {
    minWidth: 52,
    paddingHorizontal: 16,
    alignSelf: "stretch",
    alignItems: "center",
    justifyContent: "center",
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: editorialTheme.border
  },
  stepperValue: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 13,
    lineHeight: 16,
    letterSpacing: 1.6,
    textTransform: "uppercase",
    color: editorialTheme.text
  }
});
