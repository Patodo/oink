// 发布构建在 Windows 上不弹控制台窗口。
#![cfg_attr(all(windows, not(debug_assertions)), windows_subsystem = "windows")]

fn main() -> std::process::ExitCode {
    oink_agent::telemetry::fatal_boundary(run)
}

fn run() -> std::process::ExitCode {
    #[cfg(all(windows, feature = "windows-portable"))]
    if let Err(error) = initialize_portable() {
        eprintln!("Oink Portable: {error}");
        return std::process::ExitCode::FAILURE;
    }
    if let Err(error) = oink_foundation::process::initialize_priority() {
        eprintln!("Oink process priority initialization failed: {error}");
        return std::process::ExitCode::FAILURE;
    }
    #[cfg(windows)]
    if let Some(code) = oink_agent::dispatch_raw_clip_guard() {
        return code;
    }
    #[cfg(windows)]
    if let Some(code) = oink_agent::paste_file::dispatch_shell_args() {
        return code;
    }
    // Backend/maintenance roles finish before any interactive shell is created.
    if let Some(code) = oink_ui::service::dispatch_args() {
        return code;
    }
    #[cfg(windows)]
    if let Err(error) = oink_ui::service::require_normal_user_ui() {
        eprintln!("{error}");
        return std::process::ExitCode::FAILURE;
    }
    #[cfg(windows)]
    if !oink_agent::WINDOWS_PORTABLE
        && let Some(code) = oink_ui::installer_finish::dispatch_args()
    {
        return code;
    }
    if let Some(code) = oink_autostart::handle_autostart_arg() {
        return code;
    }
    #[cfg(any(target_os = "macos", windows))]
    {
        oink_ui::run();
        std::process::ExitCode::SUCCESS
    }
    #[cfg(not(any(target_os = "macos", windows)))]
    {
        eprintln!("Oink 界面只支持 macOS 与 Windows");
        std::process::ExitCode::FAILURE
    }
}

#[cfg(all(windows, feature = "windows-portable"))]
fn initialize_portable() -> std::io::Result<()> {
    use oink_foundation::paths::StoragePaths;

    oink_winsvc::backend::require_elevated_interactive()?;
    let exe = std::env::current_exe()?;
    let directory = exe
        .parent()
        .ok_or_else(|| std::io::Error::other("missing executable directory"))?;
    let data = directory.join("Data");
    std::fs::create_dir_all(&data)?;
    StoragePaths::set_process_roots(StoragePaths::isolated(data)).map_err(std::io::Error::other)
}
