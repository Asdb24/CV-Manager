import type { ReactNode } from "react";
import { headers } from "next/headers";
import { UIProvider } from "@cv/ui";
import "@cv/ui/styles.css";

export const metadata = {
  title: "Cơ hội việc làm",
  description: "Trang tuyển dụng công khai đang được thiết lập.",
};
export default async function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  await headers();
  return (
    <html lang="vi">
      <body>
        <UIProvider>{children}</UIProvider>
      </body>
    </html>
  );
}
