import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { useQuery } from "convex/react";
import * as ImagePicker from "expo-image-picker";
import React from "react";

import { FashionTryOnScreen } from "./FashionTryOnScreen";

jest.mock("convex/react", () => {
  const actual = jest.requireActual("convex/react");

  return {
    ...actual,
    useMutation: jest.fn(),
    useQuery: jest.fn(),
  };
});

describe("App", () => {
  const useMutationMock = jest.requireMock("convex/react").useMutation as jest.Mock;
  const useQueryMock = useQuery as jest.Mock;

  beforeEach(() => {
    jest.spyOn(ImagePicker, "requestMediaLibraryPermissionsAsync").mockResolvedValue({
      canAskAgain: true,
      expires: "never",
      granted: true,
      status: ImagePicker.PermissionStatus.GRANTED,
      accessPrivileges: "all",
    });
    jest.spyOn(ImagePicker, "launchImageLibraryAsync").mockResolvedValue({
      canceled: false,
      assets: [
        {
          assetId: "asset-1",
          fileName: "look.jpg",
          fileSize: 123,
          height: 400,
          mimeType: "image/jpeg",
          type: "image",
          uri: "file:///look.jpg",
          width: 300,
        },
      ],
    });
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("keeps Generate disabled until both a photo and garment are selected", () => {
    useMutationMock.mockReturnValue(jest.fn());
    useQueryMock.mockReturnValue(undefined);

    render(<FashionTryOnScreen />);

    expect(
      screen.getByRole("button", { name: "Generate" }).props.accessibilityState
        ?.disabled,
    ).toBe(true);
  });

  it("shows loading and final result states from the render request subscription", async () => {
    let requestState:
      | undefined
      | { garmentLabel: string; resultImageUrl?: string; status: "pending" | "done" } =
      undefined;
    let resolveRequestId: ((value: string) => void) | undefined;
    const requestPromise = new Promise<string>((resolve) => {
      resolveRequestId = resolve;
    });

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        blob: async () => new Blob(["photo"], { type: "image/jpeg" }),
      })
      .mockResolvedValueOnce({
        json: async () => ({ storageId: "storage-id" }),
        ok: true,
      });

    const uploadMutation = jest.fn().mockResolvedValue("upload-url");
    const createMutation = jest.fn().mockImplementation(() => {
      requestState = {
        garmentLabel: "Beige Trench Coat",
        status: "pending",
      };
      return requestPromise;
    });
    let mutationCall = 0;

    useMutationMock.mockImplementation(() => {
      if (mutationCall % 2 === 0) {
        mutationCall += 1;
        return uploadMutation;
      }

      mutationCall += 1;
      return createMutation;
    });

    useQueryMock.mockImplementation(() => requestState);

    const view = render(<FashionTryOnScreen />);

    fireEvent.press(screen.getByRole("button", { name: "Choose Photo" }));
    fireEvent.press(screen.getByRole("button", { name: "Beige Trench Coat" }));
    fireEvent.press(screen.getByRole("button", { name: "Generate" }));

    requestState = {
      garmentLabel: "Beige Trench Coat",
      status: "pending",
    };
    resolveRequestId?.("request-id");
    view.rerender(<FashionTryOnScreen />);

    await waitFor(() => {
      expect(screen.getByText("Generating image...")).toBeTruthy();
    });

    requestState = {
      garmentLabel: "Beige Trench Coat",
      resultImageUrl: "https://example.com/final.png",
      status: "done",
    };
    view.rerender(<FashionTryOnScreen />);

    await waitFor(() => {
      expect(screen.getByText("Generated look")).toBeTruthy();
    });
  });
});
