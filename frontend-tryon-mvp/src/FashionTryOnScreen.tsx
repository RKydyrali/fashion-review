import * as ImagePicker from "expo-image-picker";
import { useMutation, useQuery } from "convex/react";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  createRenderRequestRef,
  generateUploadUrlRef,
  getRenderRequestRef,
} from "./lib/convexRefs";
import { GARMENTS } from "./lib/garments";

type PickedPhoto = {
  mimeType?: string;
  uri: string;
};

type UploadResponse = {
  storageId: string;
};

async function uploadPhoto(uploadUrl: string, photo: PickedPhoto) {
  const localFileResponse = await fetch(photo.uri);
  const blob = await localFileResponse.blob();

  const response = await fetch(uploadUrl, {
    body: blob,
    headers: {
      "Content-Type": photo.mimeType ?? "image/jpeg",
    },
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Photo upload failed (${response.status})`);
  }

  return (await response.json()) as UploadResponse;
}

export function FashionTryOnScreen({
  missingConfig,
}: {
  missingConfig?: string;
}) {
  const [pickedPhoto, setPickedPhoto] = useState<PickedPhoto | null>(null);
  const [selectedGarmentId, setSelectedGarmentId] = useState<string | null>(
    null,
  );
  const [requestId, setRequestId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const generateUploadUrl = useMutation(generateUploadUrlRef);
  const createRenderRequest = useMutation(createRenderRequestRef);
  const renderRequest = useQuery(
    getRenderRequestRef,
    requestId ? { requestId: requestId as any } : "skip",
  );

  const selectedGarment = GARMENTS.find(
    (garment) => garment.id === selectedGarmentId,
  );

  async function handleChoosePhoto() {
    const permission =
      await ImagePicker.requestMediaLibraryPermissionsAsync();

    if (!permission.granted) {
      Alert.alert("Permission needed", "Photo library access is required.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: false,
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (result.canceled || !result.assets[0]) {
      return;
    }

    setPickedPhoto({
      mimeType: result.assets[0].mimeType,
      uri: result.assets[0].uri,
    });
    setRequestId(null);
  }

  async function handleGenerate() {
    if (!pickedPhoto || !selectedGarment) {
      return;
    }

    try {
      setIsSubmitting(true);

      const uploadUrl = await generateUploadUrl({});
      const uploadResult = await uploadPhoto(uploadUrl, pickedPhoto);
      const newRequestId = await createRenderRequest({
        garmentId: selectedGarment.id,
        garmentImageUrl: selectedGarment.imageUrl,
        userImageStorageId: uploadResult.storageId as any,
      });

      setRequestId(newRequestId as string);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Generation failed";
      Alert.alert("Generation failed", message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const isPending = isSubmitting || renderRequest?.status === "pending";
  const generatedImageUrl =
    renderRequest?.status === "done" ? renderRequest.resultImageUrl : undefined;
  const errorMessage =
    renderRequest?.status === "error" ? renderRequest.errorMessage : undefined;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Fashion Try-On MVP</Text>
      <Text style={styles.subtitle}>
        Upload one photo, choose one garment, and generate one look.
      </Text>

      {missingConfig ? (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Configuration needed</Text>
          <Text style={styles.helperText}>
            Set {missingConfig} before launching the app.
          </Text>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>1. Photo</Text>
        <Pressable
          accessibilityRole="button"
          onPress={handleChoosePhoto}
          style={styles.primaryButton}
        >
          <Text style={styles.primaryButtonText}>Choose Photo</Text>
        </Pressable>
        {pickedPhoto ? (
          <Image source={{ uri: pickedPhoto.uri }} style={styles.previewImage} />
        ) : (
          <Text style={styles.helperText}>No photo selected yet.</Text>
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>2. Garment</Text>
        {GARMENTS.map((garment) => {
          const selected = garment.id === selectedGarmentId;

          return (
            <Pressable
              accessibilityRole="button"
              key={garment.id}
              onPress={() => setSelectedGarmentId(garment.id)}
              style={[styles.garmentButton, selected && styles.garmentSelected]}
            >
              <Text style={styles.garmentText}>{garment.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>3. Generate</Text>
        <Pressable
          accessibilityRole="button"
          disabled={!pickedPhoto || !selectedGarment || isSubmitting}
          onPress={handleGenerate}
          style={[
            styles.primaryButton,
            (!pickedPhoto || !selectedGarment || isSubmitting) &&
              styles.buttonDisabled,
          ]}
        >
          <Text style={styles.primaryButtonText}>Generate</Text>
        </Pressable>
      </View>

      {isPending ? (
        <View style={styles.card}>
          <ActivityIndicator />
          <Text style={styles.helperText}>Generating image...</Text>
        </View>
      ) : null}

      {errorMessage ? (
        <View style={styles.card}>
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : null}

      {generatedImageUrl ? (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Generated look</Text>
          <Image
            source={{ uri: generatedImageUrl }}
            style={styles.previewImage}
          />
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  buttonDisabled: {
    opacity: 0.45,
  },
  card: {
    backgroundColor: "#ffffff",
    borderColor: "#e5e7eb",
    borderRadius: 16,
    borderWidth: 1,
    gap: 12,
    padding: 16,
    width: "100%",
  },
  container: {
    alignItems: "center",
    backgroundColor: "#f4f4f5",
    gap: 16,
    minHeight: "100%",
    padding: 20,
    paddingTop: 72,
  },
  errorText: {
    color: "#b91c1c",
  },
  garmentButton: {
    backgroundColor: "#f4f4f5",
    borderColor: "#d4d4d8",
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  garmentSelected: {
    backgroundColor: "#111827",
    borderColor: "#111827",
  },
  garmentText: {
    color: "#111827",
    fontSize: 15,
  },
  helperText: {
    color: "#52525b",
    fontSize: 14,
  },
  previewImage: {
    aspectRatio: 1,
    borderRadius: 14,
    width: "100%",
  },
  primaryButton: {
    alignItems: "center",
    backgroundColor: "#111827",
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 14,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "600",
  },
  sectionTitle: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "600",
  },
  subtitle: {
    color: "#52525b",
    fontSize: 15,
    marginBottom: 8,
    textAlign: "center",
  },
  title: {
    color: "#111827",
    fontSize: 28,
    fontWeight: "700",
  },
});
