import { StrictMode, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Button, UIProvider, StatusMessage } from "@cv/ui";
import { staffClient } from "@cv/api-client/staff";
import "@cv/ui/styles.css";

const configuration = __CLIENT_CONFIGURATION__;
const client = staffClient(
  configuration.api_origin,
  configuration.request_timeout_ms,
);

function Shell() {
  const [page, setPage] = useState<"overview" | "connection">("overview");
  const [state, setState] = useState<
    "idle" | "loading" | "responded" | "error"
  >("idle");
  const [message, setMessage] = useState(
    "Chưa kiểm tra kết nối. Đăng nhập và quản lý hồ sơ chưa khả dụng.",
  );
  const pending = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      pending.current?.abort();
    },
    [],
  );
  function select(next: "overview" | "connection") {
    pending.current?.abort();
    pending.current = null;
    setState("idle");
    setMessage(
      "Chưa kiểm tra kết nối. Đăng nhập và quản lý hồ sơ chưa khả dụng.",
    );
    setPage(next);
  }
  async function check() {
    if (state === "loading") return;
    const operation = new AbortController();
    pending.current = operation;
    setState("loading");
    setMessage("Đang kiểm tra kết nối…");
    try {
      const result = await client.GET("/live", { signal: operation.signal });
      if (pending.current !== operation || operation.signal.aborted) return;
      if (!result.data?.alive) throw new Error("SERVICE_UNAVAILABLE");
      setState("responded");
      setMessage(
        "Dịch vụ có phản hồi. Đăng nhập, dữ liệu và tài liệu chưa khả dụng.",
      );
    } catch {
      if (pending.current !== operation || operation.signal.aborted) return;
      setState("error");
      setMessage("Không kết nối được dịch vụ. Kiểm tra kết nối và thử lại.");
    }
  }
  return (
    <div className="desktop-layout">
      <aside className="sidebar">
        <div className="brand">Hồ sơ tuyển dụng</div>
        <nav aria-label="Điều hướng">
          <Button
            appearance={page === "overview" ? "primary" : "subtle"}
            onClick={() => {
              select("overview");
            }}
          >
            Tổng quan
          </Button>
          <Button
            appearance={page === "connection" ? "primary" : "subtle"}
            onClick={() => {
              select("connection");
            }}
          >
            Kết nối
          </Button>
        </nav>
      </aside>
      <main className="workspace">
        <header className="workspace-header">
          <span>
            {configuration.execution_mode === "standalone"
              ? "Không gian cục bộ"
              : "Không gian kết nối"}
          </span>
          <span className="shell-label">Bản khung giao diện</span>
        </header>
        <section className="content-heading">
          <h1>
            {page === "overview"
              ? "Quản lý hồ sơ tuyển dụng"
              : "Kết nối dịch vụ"}
          </h1>
          <p>Chuẩn bị không gian làm việc cho đội ngũ tuyển dụng.</p>
        </section>
        <section className="empty-content">
          <h2>
            {page === "overview"
              ? "Chức năng hồ sơ chưa khả dụng"
              : "Kiểm tra trước khi làm việc"}
          </h2>
          <p>
            Giao diện hiện tại chưa hỗ trợ đăng nhập, tải CV hoặc đánh giá ứng
            viên.
          </p>
          <Button
            appearance="primary"
            onClick={() => {
              void check();
            }}
            disabled={state === "loading"}
          >
            Kiểm tra kết nối
          </Button>
          <StatusMessage state={state} message={message} />
        </section>
      </main>
    </div>
  );
}

const element = document.getElementById("root");
if (!element) throw new Error("SHELL_ROOT_MISSING");
createRoot(element).render(
  <StrictMode>
    <UIProvider>
      <Shell />
    </UIProvider>
  </StrictMode>,
);
