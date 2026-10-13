"use client";

import { useEffect, useRef, useState } from "react";
import { Button, StatusMessage } from "@cv/ui";

export default function PublicShell() {
  const [state, setState] = useState<
    "idle" | "loading" | "responded" | "error"
  >("idle");
  const [message, setMessage] = useState(
    "Danh sách vị trí và biểu mẫu ứng tuyển chưa khả dụng.",
  );
  const pending = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      pending.current?.abort();
    },
    [],
  );
  async function check() {
    if (state === "loading") return;
    const operation = new AbortController();
    pending.current = operation;
    setState("loading");
    setMessage("Đang kiểm tra kết nối…");
    try {
      const timeout = Number(process.env["NEXT_PUBLIC_REQUEST_TIMEOUT_MS"]);
      if (!Number.isSafeInteger(timeout) || timeout <= 0)
        throw new Error("CONFIGURATION_INVALID");
      const response = await fetch("/api/status", {
        signal: AbortSignal.any([
          operation.signal,
          AbortSignal.timeout(timeout),
        ]),
        credentials: "omit",
        redirect: "error",
      });
      if (operation.signal.aborted || pending.current !== operation) return;
      if (!response.ok) throw new Error("PUBLIC_SERVICE_UNAVAILABLE");
      setState("responded");
      setMessage("Dịch vụ có phản hồi. Tra cứu và ứng tuyển chưa khả dụng.");
    } catch {
      if (operation.signal.aborted || pending.current !== operation) return;
      setState("error");
      setMessage("Không kết nối được dịch vụ. Vui lòng thử lại sau.");
    }
  }
  return (
    <>
      <header className="public-header">
        <span className="brand">Tuyển dụng</span>
        <span className="shell-label">Bản khung giao diện</span>
      </header>
      <main className="public-main">
        <h1>Cơ hội việc làm</h1>
        <p>Trang tuyển dụng đang được thiết lập.</p>
        <section className="empty-content">
          <h2>Danh sách việc làm chưa khả dụng</h2>
          <p>
            Các vị trí được công bố sẽ xuất hiện tại đây khi dịch vụ sẵn sàng.
          </p>
          <Button
            appearance="primary"
            disabled={state === "loading"}
            onClick={() => {
              void check();
            }}
          >
            Kiểm tra kết nối
          </Button>
          <StatusMessage state={state} message={message} />
        </section>
      </main>
      <footer className="public-footer">
        Trang này chưa nhận thông tin liên hệ hoặc CV.
      </footer>
    </>
  );
}
