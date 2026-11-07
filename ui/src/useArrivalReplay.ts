import { useEffect, useState } from "react";

export function useArrivalReplay(total: number) {
  const [state, setState] = useState<{
    count: number;
    playing: boolean;
    revealed: boolean;
  } | null>(null);
  useEffect(() => {
    if (!state?.playing || state.count >= total) return;
    const timer = setTimeout(
      () =>
        setState((previous) =>
          previous
            ? {
                ...previous,
                count: previous.count + 1,
                playing: previous.count + 1 < total,
              }
            : previous,
        ),
      650,
    );
    return () => clearTimeout(timer);
  }, [state?.count, state?.playing, total]);
  return {
    active: state !== null,
    count: state?.count || 0,
    playing: state?.playing || false,
    revealed: state?.revealed || false,
    start: () => setState({ count: 0, playing: true, revealed: false }),
    pause: () =>
      setState((previous) =>
        previous ? { ...previous, playing: !previous.playing } : previous,
      ),
    reveal: () =>
      setState((previous) =>
        previous && previous.count === total
          ? { ...previous, revealed: true }
          : previous,
      ),
    stop: () => setState(null),
  };
}
