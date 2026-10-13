"use client";

import { FluentProvider } from "@fluentui/react-provider";
import { Button } from "@fluentui/react-button";
import { Text } from "@fluentui/react-text";
import { webDarkTheme, webLightTheme } from "@fluentui/react-theme";
import { useEffect, useState, type PropsWithChildren } from "react";
import { Cross2Icon, InfoCircledIcon, ReloadIcon } from "@radix-ui/react-icons";

export { Button, Text };

export function UIProvider({ children }: PropsWithChildren) {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const preference = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      setDark(preference.matches);
    };
    update();
    preference.addEventListener("change", update);
    return () => {
      preference.removeEventListener("change", update);
    };
  }, []);
  return (
    <FluentProvider
      theme={
        dark
          ? webDarkTheme
          : { ...webLightTheme, colorNeutralBackground1: "#fcfcfd" }
      }
      className="cv-theme"
      data-theme={dark ? "dark" : "light"}
    >
      {children}
    </FluentProvider>
  );
}

export function StatusMessage({
  state,
  message,
}: {
  state: "idle" | "loading" | "responded" | "error";
  message: string;
}) {
  return (
    <div
      className={`status-message status-${state}`}
      role={state === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      {state === "loading" ? (
        <ReloadIcon aria-hidden="true" />
      ) : state === "error" ? (
        <Cross2Icon aria-hidden="true" />
      ) : (
        <InfoCircledIcon aria-hidden="true" />
      )}
      <span>{message}</span>
    </div>
  );
}
