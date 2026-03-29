import { PropsWithChildren } from "react";
import { Pressable, StyleProp, StyleSheet, Text, TextInput, TextStyle, View, ViewStyle } from "react-native";

import { editorialTheme, editorialSerif } from "@/components/ui";

export const adminPalette = {
  accentSurface: "#EEE7DB",
  accentSurfaceStrong: "#E3D7C3",
  accentBorder: "#C5B290",
  accentText: "#6A5431",
  greenSurface: "#E8EEE6",
  roseSurface: "#F4E8E4"
} as const;

export function AdminHero({
  eyebrow,
  title,
  description,
  children,
  style
}: PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  style?: StyleProp<ViewStyle>;
}>) {
  return (
    <View style={[styles.hero, style]}>
      <Text style={styles.heroEyebrow}>{eyebrow}</Text>
      <Text style={styles.heroTitle}>{title}</Text>
      <Text style={styles.heroDescription}>{description}</Text>
      {children ? <View style={styles.heroBody}>{children}</View> : null}
    </View>
  );
}

export function AdminStatGrid({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return <View style={[styles.statGrid, style]}>{children}</View>;
}

export function AdminStatCard({
  label,
  value,
  note,
  tone = "default",
  style
}: {
  label: string;
  value: string;
  note?: string;
  tone?: "default" | "accent" | "success" | "danger";
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View
      style={[
        styles.statCard,
        tone === "accent" ? styles.statCardAccent : null,
        tone === "success" ? styles.statCardSuccess : null,
        tone === "danger" ? styles.statCardDanger : null,
        style
      ]}
    >
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
      {note ? <Text style={styles.statNote}>{note}</Text> : null}
    </View>
  );
}

export function AdminSection({
  title,
  description,
  children,
  style
}: PropsWithChildren<{
  title: string;
  description?: string;
  style?: StyleProp<ViewStyle>;
}>) {
  return (
    <View style={[styles.section, style]}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {description ? <Text style={styles.sectionDescription}>{description}</Text> : null}
      </View>
      <View style={styles.sectionBody}>{children}</View>
    </View>
  );
}

export function AdminField({
  label,
  value,
  onChangeText,
  multiline,
  placeholder,
  keyboardType,
  style
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  multiline?: boolean;
  placeholder?: string;
  keyboardType?: "default" | "email-address" | "numeric";
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={style}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        multiline={multiline}
        placeholder={placeholder}
        keyboardType={keyboardType}
        placeholderTextColor={editorialTheme.textSoft}
        style={[styles.input, multiline ? styles.multilineInput : null]}
        autoCapitalize="none"
      />
    </View>
  );
}

export function AdminOptionGroup({
  label,
  options,
  activeValue,
  onChange,
  style
}: {
  label: string;
  options: Array<{ label: string; value: string }>;
  activeValue: string;
  onChange: (value: string) => void;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={style}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.optionWrap}>
        {options.map((option) => {
          const active = activeValue === option.value;
          return (
            <Pressable key={option.value} style={[styles.optionChip, active ? styles.optionChipActive : null]} onPress={() => onChange(option.value)}>
              <Text style={[styles.optionText, active ? styles.optionTextActive : null]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export function AdminToggle({
  label,
  value,
  onToggle,
  style
}: {
  label: string;
  value: boolean;
  onToggle: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <Pressable style={[styles.toggleRow, style]} onPress={onToggle}>
      <Text style={styles.toggleLabel}>{label}</Text>
      <View style={[styles.togglePill, value ? styles.togglePillActive : null]}>
        <Text style={[styles.toggleText, value ? styles.toggleTextActive : null]}>{value ? "On" : "Off"}</Text>
      </View>
    </Pressable>
  );
}

export function AdminFormTitle({ children, style }: PropsWithChildren<{ style?: StyleProp<TextStyle> }>) {
  return <Text style={[styles.formTitle, style]}>{children}</Text>;
}

export function AdminEmptyState({
  title,
  description,
  style
}: {
  title: string;
  description: string;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[styles.emptyState, style]}>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyDescription}>{description}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    borderWidth: 1,
    borderColor: adminPalette.accentBorder,
    backgroundColor: adminPalette.accentSurface,
    padding: 22,
    gap: 10,
    borderRadius: 2
  },
  heroEyebrow: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2.8,
    textTransform: "uppercase",
    color: adminPalette.accentText
  },
  heroTitle: {
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 34,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  heroDescription: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 15,
    lineHeight: 26,
    color: editorialTheme.textMuted
  },
  heroBody: {
    marginTop: 6,
    gap: 12
  },
  statGrid: {
    gap: 12
  },
  statCard: {
    minHeight: 112,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    padding: 16,
    justifyContent: "space-between",
    borderRadius: 2
  },
  statCardAccent: {
    backgroundColor: adminPalette.accentSurfaceStrong,
    borderColor: adminPalette.accentBorder
  },
  statCardSuccess: {
    backgroundColor: adminPalette.greenSurface
  },
  statCardDanger: {
    backgroundColor: adminPalette.roseSurface
  },
  statLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 2,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  statValue: {
    fontFamily: editorialSerif,
    fontSize: 24,
    lineHeight: 28,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  statNote: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 18,
    color: editorialTheme.textMuted
  },
  section: {
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    padding: 20,
    borderRadius: 2
  },
  sectionHeader: {
    gap: 6
  },
  sectionTitle: {
    fontFamily: editorialSerif,
    fontSize: 22,
    lineHeight: 26,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  sectionDescription: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 22,
    color: editorialTheme.textMuted
  },
  sectionBody: {
    gap: 16,
    marginTop: 18
  },
  fieldLabel: {
    marginBottom: 8,
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.textSoft
  },
  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 14,
    color: editorialTheme.text
  },
  multilineInput: {
    minHeight: 108,
    textAlignVertical: "top"
  },
  optionWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  optionChip: {
    minHeight: 40,
    paddingHorizontal: 14,
    justifyContent: "center",
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surface,
    borderRadius: 999
  },
  optionChipActive: {
    borderColor: editorialTheme.text,
    backgroundColor: editorialTheme.text
  },
  optionText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  optionTextActive: {
    color: editorialTheme.surface
  },
  toggleRow: {
    minHeight: 54,
    borderWidth: 1,
    borderColor: editorialTheme.border,
    backgroundColor: editorialTheme.surfaceMuted,
    paddingHorizontal: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  toggleLabel: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  togglePill: {
    minWidth: 58,
    minHeight: 30,
    borderWidth: 1,
    borderColor: editorialTheme.borderStrong,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
    backgroundColor: editorialTheme.surface
  },
  togglePillActive: {
    backgroundColor: editorialTheme.text,
    borderColor: editorialTheme.text
  },
  toggleText: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  toggleTextActive: {
    color: editorialTheme.surface
  },
  formTitle: {
    fontFamily: editorialSerif,
    fontSize: 30,
    lineHeight: 34,
    letterSpacing: 1.4,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  emptyState: {
    borderWidth: 1,
    borderStyle: "dashed",
    borderColor: editorialTheme.borderStrong,
    backgroundColor: editorialTheme.surfaceMuted,
    padding: 18,
    gap: 8,
    borderRadius: 2
  },
  emptyTitle: {
    fontFamily: "SpaceGrotesk_500Medium",
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 1.8,
    textTransform: "uppercase",
    color: editorialTheme.text
  },
  emptyDescription: {
    fontFamily: "SpaceGrotesk_400Regular",
    fontSize: 13,
    lineHeight: 22,
    color: editorialTheme.textMuted
  }
});
