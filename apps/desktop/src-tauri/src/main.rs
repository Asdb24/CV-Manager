#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

#[cfg(debug_assertions)]
use tauri::Manager;

fn main() {
    // Phase 02 shell only: no native HTTP, service bootstrap, login or filesystem authority.
    tauri::Builder::default()
        .setup(|app| {
            // Debug-only inspection fixture uses the required Phase 02 acceptance viewport.
            #[cfg(debug_assertions)]
            if std::env::args().any(|arg| arg == "--inspection-small-window") {
                let window = app
                    .get_webview_window("main")
                    .ok_or("SHELL_WINDOW_MISSING")?;
                window.set_size(tauri::LogicalSize::new(1024.0, 768.0))?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("SHELL_START_FAILED");
}
