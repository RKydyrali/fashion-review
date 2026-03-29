import { useMutation } from "@tanstack/react-query";
import { Text } from "react-native";

import { BodyText, CardFrame, EditorialButton, EditorialTitle, Screen, SectionLabel } from "@/components/ui";
import { useI18n } from "@/i18n";
import { apiFetch } from "@/services/api/client";

type CapsuleResponse = {
  summary: string;
  outfits: Array<{ explanation: string; items: Array<{ id: number; name: string }> }>;
};

export default function CapsuleScreen() {
  const { t } = useI18n();
  const capsule = useMutation({
    mutationFn: () =>
      apiFetch<CapsuleResponse>("/api/v1/wardrobes/capsule", {
        method: "POST",
        body: JSON.stringify({ season: "summer", max_outfits: 3, target_item_limit: 6 })
      })
  });

  return (
    <Screen>
      <SectionLabel>{t("capsule.section", "Capsule Builder")}</SectionLabel>
      <EditorialTitle>{t("capsule.title", "Build a quiet capsule.")}</EditorialTitle>
      <BodyText>{t("capsule.intro", "Generates looks from the live wardrobe endpoint and keeps the output session-based for now.")}</BodyText>
      <EditorialButton label={t("capsule.generate", "Generate Capsule")} onPress={() => capsule.mutate()} />
      {capsule.data?.outfits.map((outfit, index) => (
        <CardFrame key={`${outfit.explanation}-${index}`}>
          <Text className="font-bold text-[22px] text-ink">{t("capsule.look", "Look {index}", { index: index + 1 })}</Text>
          <BodyText>{outfit.explanation}</BodyText>
          {outfit.items.map((item) => (
            <Text key={item.id} className="mt-2 text-[16px] text-ink">{item.name}</Text>
          ))}
        </CardFrame>
      ))}
    </Screen>
  );
}
