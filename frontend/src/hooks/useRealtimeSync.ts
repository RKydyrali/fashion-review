import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { WS_BASE_URL } from "@/config/env";
import { useAuthStore } from "@/state/auth-store";

export function useRealtimeSync() {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    const socket = new WebSocket(`${WS_BASE_URL}/ws/updates?token=${accessToken}`);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { event?: string };
      if (payload.event?.startsWith("order_")) {
        queryClient.invalidateQueries({ queryKey: ["orders"] });
        queryClient.invalidateQueries({ queryKey: ["preorders"] });
      }
      if (payload.event?.startsWith("try_on_")) {
        queryClient.invalidateQueries({ queryKey: ["try-on"] });
      }
    };
    return () => socket.close();
  }, [accessToken, queryClient]);
}
