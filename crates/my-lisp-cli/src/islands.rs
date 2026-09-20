use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

use serde::Deserialize;

const REMOTE_MANIFEST_URL: &str =
    "https://github.com/juv4uk/my-lisp/releases/latest/download/islands-manifest-v1.json";

#[derive(Deserialize)]
struct Manifest {
    protocol: String,
    #[serde(default)]
    profiles: Vec<Profile>,
    islands: Vec<Island>,
}

#[derive(Deserialize)]
struct Profile {
    key: String,
    islands: Vec<String>,
}

#[derive(Deserialize)]
struct Island {
    key: String,
    runtime_version: String,
    abi_compatibility: String,
    install_key: String,
    license: String,
    license_acceptance_required: bool,
    provenance: String,
    platforms: Vec<PlatformEntry>,
}

#[derive(Deserialize)]
struct PlatformEntry {
    target: String,
    provider: String,
    package: Option<String>,
    package_version: Option<String>,
    url: Option<String>,
    checksum_algorithm: Option<String>,
    sha256: Option<String>,
    artifact_format: Option<String>,
    entrypoint: Option<String>,
    reason: Option<String>,
    artifact: Option<String>,
    #[serde(default)]
    installer_args: Vec<String>,
    #[serde(default)]
    probe: Vec<String>,
    probe_expect: Option<String>,
}

fn bounded_probe(command: &[String], expected: Option<&str>) -> &'static str {
    let Some(program) = command.first() else {
        return "probe-failed";
    };
    let mut child = match Command::new(program)
        .args(&command[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => return "probe-failed",
    };

    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        match child.try_wait() {
            Ok(Some(status)) if status.success() => {
                let output = match child.wait_with_output() {
                    Ok(output) => output,
                    Err(_) => return "probe-failed",
                };
                if expected
                    .map(|needle| {
                        String::from_utf8_lossy(&output.stdout).contains(needle)
                            || String::from_utf8_lossy(&output.stderr).contains(needle)
                    })
                    .unwrap_or(true)
                {
                    return "available";
                }
                return "probe-failed";
            }
            Ok(Some(_)) => return "probe-failed",
            Ok(None) if Instant::now() < deadline => {
                std::thread::sleep(Duration::from_millis(25));
            }
            _ => {
                let _ = child.kill();
                let _ = child.wait();
                return "probe-failed";
            }
        }
    }
}

fn fetch_artifact(url: &str, temporary: &Path) -> Result<(), String> {
    if let Some(source) = url.strip_prefix("file://") {
        fs::copy(source, temporary)
            .map_err(|error| format!("cannot read artifact {source}: {error}"))?;
        return Ok(());
    }
    if !(url.starts_with("https://") || url.starts_with("http://")) {
        return Err("installer supports file:// and http(s):// release assets only".to_string());
    }

    let output = temporary.to_string_lossy().into_owned();
    match Command::new("curl")
        .args([
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            "120",
            "--output",
            &output,
            url,
        ])
        .status()
    {
        Ok(status) if status.success() => Ok(()),
        Ok(status) => Err(format!("download failed for {url}: curl exit {status}")),
        Err(curl_error) if cfg!(windows) => {
            let status = Command::new("powershell")
                .args([
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri $env:MY_LISP_URL -OutFile $env:MY_LISP_OUT",
                ])
                .env("MY_LISP_URL", url)
                .env("MY_LISP_OUT", &output)
                .status()
                .map_err(|error| {
                    format!(
                        "download failed for {url}: curl unavailable ({curl_error}); powershell failed: {error}"
                    )
                })?;
            if status.success() {
                Ok(())
            } else {
                Err(format!("download failed for {url}: powershell exit {status}"))
            }
        }
        Err(curl_error) if cfg!(target_os = "linux") => {
            if let Ok(status) = Command::new("wget")
                .args(["--quiet", "--output-document", &output, url])
                .status()
            {
                if status.success() {
                    return Ok(());
                }
            }

            let apt_available = Command::new("apt-get")
                .arg("--version")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status()
                .map(|status| status.success())
                .unwrap_or(false);
            if !apt_available {
                return Err(format!(
                    "download failed for {url}: curl unavailable ({curl_error}), wget unavailable, and apt-get is unavailable"
                ));
            }

            let mut install = if running_as_root() {
                Command::new("apt-get")
            } else {
                let mut command = Command::new("sudo");
                command.arg("env");
                command.arg("DEBIAN_FRONTEND=noninteractive");
                command.arg("apt-get");
                command
            };
            if running_as_root() {
                install.env("DEBIAN_FRONTEND", "noninteractive");
            }
            install.args(["update"]);
            run_status_command(&mut install, "apt-get update for curl bootstrap failed")?;

            let mut install = if running_as_root() {
                Command::new("apt-get")
            } else {
                let mut command = Command::new("sudo");
                command.arg("env");
                command.arg("DEBIAN_FRONTEND=noninteractive");
                command.arg("apt-get");
                command
            };
            if running_as_root() {
                install.env("DEBIAN_FRONTEND", "noninteractive");
            }
            install.args(["install", "-y", "curl"]);
            run_status_command(&mut install, "automatic curl bootstrap failed")?;

            let status = Command::new("curl")
                .args([
                    "--fail",
                    "--location",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "120",
                    "--output",
                    &output,
                    url,
                ])
                .status()
                .map_err(|error| format!("curl bootstrap succeeded but download failed for {url}: {error}"))?;
            if status.success() {
                Ok(())
            } else {
                Err(format!("download failed for {url}: curl exit {status}"))
            }
        }
        Err(error) => Err(format!("download failed for {url}: curl unavailable: {error}")),
    }
}

fn current_target() -> &'static str {
    match (std::env::consts::OS, std::env::consts::ARCH) {
        ("linux", "x86_64") => "linux-x86_64",
        ("windows", "x86_64") => "windows-x86_64",
        ("macos", "x86_64") => "macos-x86_64",
        ("macos", "aarch64") => "macos-aarch64",
        _ => "unsupported-host",
    }
}

fn value_after<'a>(args: &'a [String], option: &str) -> Option<&'a str> {
    args.iter()
        .position(|arg| arg == option)
        .and_then(|index| args.get(index + 1))
        .map(String::as_str)
}

fn install_root(args: &[String]) -> String {
    if let Some(root) = value_after(args, "--root") {
        return root.to_string();
    }

    #[cfg(windows)]
    if let Some(local_app_data) = std::env::var_os("LOCALAPPDATA") {
        return PathBuf::from(local_app_data)
            .join("my-lisp")
            .join("islands")
            .to_string_lossy()
            .into_owned();
    }

    #[cfg(not(windows))]
    if let Some(data_home) = std::env::var_os("XDG_DATA_HOME") {
        return PathBuf::from(data_home)
            .join("my-lisp")
            .join("islands")
            .to_string_lossy()
            .into_owned();
    }

    std::env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".local")
        .join("share")
        .join("my-lisp")
        .join("islands")
        .to_string_lossy()
        .into_owned()
}

fn load_manifest_file(path: &str) -> Result<Manifest, String> {
    let source =
        fs::read_to_string(path).map_err(|error| format!("cannot read manifest {path}: {error}"))?;
    let manifest: Manifest = serde_json::from_str(&source)
        .map_err(|error| format!("invalid manifest {path}: {error}"))?;

    if manifest.protocol != "my-lisp-islands-manifest/1" {
        return Err(format!("unsupported manifest protocol: {}", manifest.protocol));
    }

    let known_targets = [
        "linux-x86_64",
        "windows-x86_64",
        "macos-x86_64",
        "macos-aarch64",
    ];
    let known_providers = [
        "apt",
        "dnf",
        "brew",
        "winget",
        "release-asset",
        "embedded",
        "unsupported",
    ];
    let mut island_keys = std::collections::HashSet::new();
    let mut install_keys = std::collections::HashSet::new();
    for island in &manifest.islands {
        if island.key.is_empty() || !island_keys.insert(&island.key) {
            return Err(format!(
                "manifest has duplicate or empty island key: {}",
                island.key
            ));
        }
        if island.runtime_version.is_empty()
            || island.abi_compatibility.is_empty()
            || island.install_key.is_empty()
            || island.license.is_empty()
        {
            return Err(format!(
                "island {} is missing required release metadata",
                island.key
            ));
        }
        if !install_keys.insert(&island.install_key) {
            return Err(format!(
                "manifest has duplicate install key: {}",
                island.install_key
            ));
        }
        let mut targets = std::collections::HashSet::new();
        for entry in &island.platforms {
            if !targets.insert(&entry.target) {
                return Err(format!(
                    "island {} has duplicate target {}",
                    island.key, entry.target
                ));
            }
            if !known_targets.contains(&entry.target.as_str()) {
                return Err(format!(
                    "island {} has unsupported target {}",
                    island.key, entry.target
                ));
            }
            if !known_providers.contains(&entry.provider.as_str()) {
                return Err(format!(
                    "island {} has unsupported provider {}",
                    island.key, entry.provider
                ));
            }

            match entry.provider.as_str() {
                "release-asset" => {
                    let url = entry.url.as_deref().ok_or_else(|| {
                        format!("island {} release asset is missing URL", island.key)
                    })?;
                    if !(url.starts_with("https://")
                        || url.starts_with("http://")
                        || url.starts_with("file://"))
                    {
                        return Err(format!(
                            "island {} release asset has unsupported URL",
                            island.key
                        ));
                    }
                    if entry.checksum_algorithm.as_deref() != Some("sha256") {
                        return Err(format!(
                            "island {} release asset must declare sha256 checksum algorithm",
                            island.key
                        ));
                    }
                    let sha256 = entry.sha256.as_deref().ok_or_else(|| {
                        format!("island {} release asset is missing SHA-256", island.key)
                    })?;
                    if sha256.len() != 64
                        || !sha256.bytes().all(|byte| byte.is_ascii_hexdigit())
                    {
                        return Err(format!("island {} has invalid SHA-256", island.key));
                    }
                    if entry
                        .artifact_format
                        .as_deref()
                        .is_none_or(str::is_empty)
                    {
                        return Err(format!(
                            "island {} release asset is missing artifact format",
                            island.key
                        ));
                    }
                    if entry.entrypoint.as_deref().is_none_or(str::is_empty) {
                        return Err(format!(
                            "island {} release asset is missing entrypoint",
                            island.key
                        ));
                    }
                    if entry.probe.is_empty() {
                        return Err(format!(
                            "island {} release asset is missing a bounded probe",
                            island.key
                        ));
                    }
                }
                "unsupported" => {
                    if entry.reason.as_deref().is_none_or(str::is_empty) {
                        return Err(format!(
                            "island {} unsupported target is missing reason",
                            island.key
                        ));
                    }
                }
                "embedded" => {}
                _ => {
                    if entry.package.as_deref().is_none_or(str::is_empty) {
                        return Err(format!(
                            "island {} package provider is missing package name",
                            island.key
                        ));
                    }
                    if entry.entrypoint.as_deref().is_none_or(str::is_empty) {
                        return Err(format!(
                            "island {} package provider is missing entrypoint",
                            island.key
                        ));
                    }
                    if entry.probe.is_empty() {
                        return Err(format!(
                            "island {} package provider is missing a bounded probe",
                            island.key
                        ));
                    }
                }
            }
        }
    }
    Ok(manifest)
}

fn load_manifest(args: &[String]) -> Result<Manifest, String> {
    if let Some(path) = value_after(args, "--manifest") {
        return load_manifest_file(path);
    }

    let temporary = std::env::temp_dir().join(format!(
        "my-lisp-islands-manifest-{}-{}.json",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|duration| duration.as_nanos())
            .unwrap_or_default()
    ));
    fetch_artifact(REMOTE_MANIFEST_URL, &temporary)?;
    let result = load_manifest_file(temporary.to_str().unwrap_or_default());
    let _ = fs::remove_file(&temporary);
    result
}

fn requested_keys(manifest: &Manifest, args: &[String]) -> Result<Vec<String>, String> {
    if let Some(keys) = value_after(args, "--with") {
        let keys: Vec<String> = keys
            .split(',')
            .filter(|key| !key.is_empty())
            .map(str::to_string)
            .collect();
        if keys.is_empty() {
            return Err("--with requires at least one island key".to_string());
        }
        return Ok(keys);
    }

    if let Some(profile_key) = value_after(args, "--profile") {
        return manifest
            .profiles
            .iter()
            .find(|profile| profile.key == profile_key)
            .map(|profile| profile.islands.clone())
            .ok_or_else(|| format!("unknown island profile: {profile_key}"));
    }

    manifest
        .profiles
        .iter()
        .find(|profile| profile.key == "four-kernel")
        .map(|profile| profile.islands.clone())
        .ok_or_else(|| "manifest has no default four-kernel profile".to_string())
}

fn interpolate_command(command: &[String], root: &Path) -> Vec<String> {
    let root = root.to_string_lossy();
    command
        .iter()
        .map(|part| part.replace("{install_root}", &root))
        .collect()
}

fn run_status_command(command: &mut Command, description: &str) -> Result<(), String> {
    let status = command
        .status()
        .map_err(|error| format!("{description}: {error}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("{description}: exit {status}"))
    }
}

fn command_output_contains(command: &mut Command, needle: &str) -> bool {
    command
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .output()
        .map(|output| {
            output.status.success() && String::from_utf8_lossy(&output.stdout).contains(needle)
        })
        .unwrap_or(false)
}

fn system_package_available(entry: &PlatformEntry) -> bool {
    if entry.probe.is_empty() {
        return false;
    }
    let probe = entry.probe.clone();
    bounded_probe(&probe, entry.probe_expect.as_deref()) == "available"
}

#[cfg(unix)]
fn running_as_root() -> bool {
    Command::new("id")
        .arg("-u")
        .output()
        .ok()
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|value| value.trim() == "0")
        .unwrap_or(false)
}

#[cfg(not(unix))]
fn running_as_root() -> bool {
    false
}

fn install_system_package(island: &Island, entry: &PlatformEntry) -> Result<String, String> {
    let package = entry
        .package
        .as_deref()
        .ok_or_else(|| format!("system package {} has no package id", island.key))?;

    if system_package_available(entry) {
        return Ok(format!("already available {} {}", island.key, island.runtime_version));
    }

    match (std::env::consts::OS, entry.provider.as_str()) {
        ("linux", "apt") => {
            if !Command::new("apt-get")
                .arg("--version")
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status()
                .map(|status| status.success())
                .unwrap_or(false)
            {
                return Err("apt-get is required for automatic Linux island bootstrap".to_string());
            }

            let mut update = if running_as_root() {
                Command::new("apt-get")
            } else {
                let mut command = Command::new("sudo");
                command.arg("apt-get");
                command
            };
            update.arg("update");
            run_status_command(&mut update, "apt-get update failed")?;

            let mut install = if running_as_root() {
                Command::new("apt-get")
            } else {
                let mut command = Command::new("sudo");
                command.arg("env");
                command.arg("DEBIAN_FRONTEND=noninteractive");
                command.arg("apt-get");
                command
            };
            if running_as_root() {
                install.env("DEBIAN_FRONTEND", "noninteractive");
            }
            install.args(["install", "-y", package]);
            run_status_command(
                &mut install,
                &format!("automatic package installation failed for {package}"),
            )?;
        }
        ("windows", "winget") => {
            let mut winget_version = Command::new("winget");
            winget_version.arg("--version");
            if !command_output_contains(&mut winget_version, "v") {
                return Err("winget is required for automatic Windows package bootstrap".to_string());
            }

            let mut install = Command::new("winget");
            install.args([
                "install",
                "--id",
                package,
                "--exact",
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity",
            ]);
            if let Some(version) = &entry.package_version {
                install.args(["--version", version]);
            }
            run_status_command(
                &mut install,
                &format!("automatic package installation failed for {package}"),
            )?;
        }
        _ => {
            return Err(format!(
                "unsupported automatic package provider {} on {}",
                entry.provider,
                std::env::consts::OS
            ));
        }
    }

    let outcome = bounded_probe(&entry.probe, entry.probe_expect.as_deref());
    if outcome == "available" {
        Ok(format!(
            "installed {} {}: available",
            island.key, island.runtime_version
        ))
    } else {
        Err(format!(
            "installed {} but bounded probe failed",
            island.key
        ))
    }
}

fn extract_archive(artifact: &str, temporary: &Path, destination: &Path) -> Result<(), String> {
    fs::create_dir_all(destination).map_err(|error| error.to_string())?;
    let args: Vec<String> = match artifact {
        "tar-gz" => vec![
            "-xzf".to_string(),
            temporary.to_string_lossy().into_owned(),
            "-C".to_string(),
            destination.to_string_lossy().into_owned(),
        ],
        "tar-bz2" => vec![
            "-xjf".to_string(),
            temporary.to_string_lossy().into_owned(),
            "-C".to_string(),
            destination.to_string_lossy().into_owned(),
        ],
        _ => return Err(format!("unsupported archive kind: {artifact}")),
    };

    let mut command = Command::new("tar");
    command.args(&args);
    run_status_command(&mut command, "archive extraction failed")
}

fn find_named_file(root: &Path, filename: &str, remaining_depth: usize) -> Option<PathBuf> {
    if remaining_depth == 0 {
        return None;
    }
    let entries = fs::read_dir(root).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_file() && path.file_name().and_then(|name| name.to_str()) == Some(filename) {
            return Some(path);
        }
        if path.is_dir() {
            if let Some(found) = find_named_file(&path, filename, remaining_depth - 1) {
                return Some(found);
            }
        }
    }
    None
}

fn write_install_record(
    target_dir: &Path,
    island: &Island,
    entry: &PlatformEntry,
) -> Result<(), String> {
    fs::create_dir_all(target_dir).map_err(|error| error.to_string())?;
    let digest = entry.sha256.as_deref().unwrap_or("not-applicable");
    let record = format!(
        "protocol=my-lisp-island-install-record/1\nisland={}\nruntime_version={}\ntarget={}\nprovider={}\nprovenance={}\nsha256={}\nverified=true\n",
        island.key, island.runtime_version, entry.target, entry.provider, island.provenance, digest
    );
    fs::write(target_dir.join("install-record.txt"), record)
        .map_err(|error| error.to_string())
}

fn install_release_asset(
    island: &Island,
    entry: &PlatformEntry,
    root: &Path,
) -> Result<String, String> {
    let url = entry
        .url
        .as_deref()
        .ok_or_else(|| format!("release asset {} has no URL", island.key))?;
    let expected = entry
        .sha256
        .as_deref()
        .ok_or_else(|| format!("release asset {} has no SHA-256", island.key))?;
    let artifact_kind = entry.artifact.as_deref().unwrap_or("file");
    let target_dir = root
        .join(&island.key)
        .join(&island.runtime_version)
        .join(&entry.target);

    if entry.probe.is_empty() {
        return Err(format!("release asset {} has no bounded probe", island.key));
    }

    let probe = interpolate_command(&entry.probe, &target_dir);
    if bounded_probe(&probe, entry.probe_expect.as_deref()) == "available" {
        return Ok(format!(
            "already available {} {}",
            island.key, island.runtime_version
        ));
    }

    let temporary = std::path::PathBuf::from(format!(
        "{}.tmp-{}",
        target_dir.display(),
        std::process::id()
    ));
    if temporary.exists() {
        let _ = fs::remove_file(&temporary);
    }

    if let Some(parent) = target_dir.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    if let Err(error) = fetch_artifact(url, &temporary) {
        let _ = fs::remove_file(&temporary);
        return Err(error);
    }

    let bytes = fs::read(&temporary).map_err(|error| error.to_string())?;
    let actual = my_lisp::sha256_source(&bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();
    if actual != expected {
        let _ = fs::remove_file(&temporary);
        return Err(format!("checksum mismatch for {}", island.key));
    }

    match artifact_kind {
        "file" => {
            let staging = target_dir.with_extension(format!("stage-{}", std::process::id()));
            if staging.exists() {
                let _ = fs::remove_dir_all(&staging);
            }
            fs::create_dir_all(&staging).map_err(|error| error.to_string())?;
            fs::rename(&temporary, staging.join("runtime.bin"))
                .map_err(|error| error.to_string())?;
            if target_dir.exists() {
                let _ = fs::remove_dir_all(&target_dir);
            }
            fs::rename(&staging, &target_dir).map_err(|error| error.to_string())?;
        }
        "tar-gz" | "tar-bz2" => {
            let staging = target_dir.with_extension(format!("stage-{}", std::process::id()));
            if staging.exists() {
                let _ = fs::remove_dir_all(&staging);
            }
            fs::create_dir_all(&staging).map_err(|error| error.to_string())?;
            extract_archive(artifact_kind, &temporary, &staging)?;
            if artifact_kind == "tar-bz2" {
                let install_script = find_named_file(&staging, "install.sh", 3)
                    .ok_or_else(|| format!("{} archive has no install.sh", island.key))?;
                let mut command = Command::new("sh");
                command.arg(&install_script);
                command.env("INSTALL_ROOT", &target_dir);
                command.current_dir(
                    install_script
                        .parent()
                        .ok_or_else(|| "invalid archive install path".to_string())?,
                );
                run_status_command(
                    &mut command,
                    &format!("{} runtime installation failed", island.key),
                )?;
            } else {
                if target_dir.exists() {
                    let _ = fs::remove_dir_all(&target_dir);
                }
                fs::rename(&staging, &target_dir).map_err(|error| error.to_string())?;
            }
        }
        "zip" => {
            let staging = target_dir.with_extension(format!("stage-{}", std::process::id()));
            if staging.exists() {
                let _ = fs::remove_dir_all(&staging);
            }
            fs::create_dir_all(&staging).map_err(|error| error.to_string())?;

            if cfg!(windows) {
                let mut command = Command::new("powershell");
                command.args([
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Expand-Archive -LiteralPath $env:MY_LISP_ZIP -DestinationPath $env:MY_LISP_DEST -Force",
                ]);
                command.env("MY_LISP_ZIP", &temporary);
                command.env("MY_LISP_DEST", &staging);
                run_status_command(&mut command, "Windows ZIP extraction failed")?;
            } else {
                let mut command = Command::new("unzip");
                command.args(["-q", &temporary.to_string_lossy(), "-d", &staging.to_string_lossy()]);
                run_status_command(&mut command, "ZIP extraction failed")?;
            }

            if target_dir.exists() {
                let _ = fs::remove_dir_all(&target_dir);
            }
            fs::rename(&staging, &target_dir).map_err(|error| error.to_string())?;
        }
        "msi" => {
            if !cfg!(windows) {
                return Err(format!("MSI release asset {} is Windows-only", island.key));
            }
            let mut command = Command::new("msiexec.exe");
            command.arg("/i").arg(&temporary).arg("/qn").arg("/norestart");
            command.args(&entry.installer_args);
            run_status_command(
                &mut command,
                &format!("MSI installation failed for {}", island.key),
            )?;
        }
        "nsis" => {
            let mut command = Command::new(&temporary);
            command.args(&entry.installer_args);
            run_status_command(
                &mut command,
                &format!("NSIS installation failed for {}", island.key),
            )?;
        }
        other => return Err(format!("unsupported release artifact kind: {other}")),
    }

    let _ = fs::remove_file(&temporary);

    let final_probe = interpolate_command(&entry.probe, &target_dir);
    let outcome = bounded_probe(&final_probe, entry.probe_expect.as_deref());
    if outcome != "available" {
        return Err(format!(
            "published {} but bounded probe failed",
            island.key
        ));
    }

    write_install_record(&target_dir, island, entry)?;

    Ok(format!(
        "installed {} {}: available",
        island.key, island.runtime_version
    ))
}

pub fn run(args: &[String]) -> Result<String, String> {
    let Some(command) = args.first().map(String::as_str) else {
        return Err(
            "usage: islands plan|install|status [--manifest <path>] [--profile key] [--with key,...] [--root path] [--dry-run]"
                .to_string(),
        );
    };

    let manifest = load_manifest(args)?;
    let target = value_after(args, "--target").unwrap_or(current_target());
    let root = PathBuf::from(install_root(args));

    match command {
        "plan" => {
            let requested = requested_keys(&manifest, args)?;
            let mut rows = Vec::new();
            for key in requested {
                let island = manifest
                    .islands
                    .iter()
                    .find(|island| island.key == key)
                    .ok_or_else(|| format!("unknown island: {key}"))?;
                let entry = island.platforms.iter().find(|entry| entry.target == target);
                let mut row = format!(
                    "island: {}\nversion: {}\nlicense: {}\nprovenance: {}\ntarget: {}",
                    island.key,
                    island.runtime_version,
                    island.license,
                    island.provenance,
                    target
                );
                match entry {
                    Some(entry) if entry.provider == "unsupported" => {
                        row.push_str(&format!(
                            "\noutcome: unsupported\nreason: {}",
                            entry.reason.as_deref().unwrap_or("not supplied")
                        ));
                    }
                    Some(entry) => {
                        row.push_str(&format!(
                            "\nprovider: {}\noutcome: installable",
                            entry.provider
                        ));
                        if let Some(package) = &entry.package {
                            row.push_str(&format!("\npackage: {package}"));
                        }
                        if let Some(package_version) = &entry.package_version {
                            row.push_str(&format!("\npackage-version: {package_version}"));
                        }
                        if let Some(url) = &entry.url {
                            row.push_str(&format!("\nurl: {url}"));
                        }
                        if let Some(sha256) = &entry.sha256 {
                            row.push_str(&format!("\nsha256:{sha256}"));
                        }
                    }
                    None => row.push_str(
                        "\noutcome: unsupported\nreason: manifest has no entry for this target",
                    ),
                }
                rows.push(row);
            }
            Ok(rows.join("\n---\n"))
        }
        "install" => {
            let dry_run = args.iter().any(|arg| arg == "--dry-run");
            let requested = requested_keys(&manifest, args)?;
            let mut rows = vec![if dry_run {
                "dry-run: no files will be created".to_string()
            } else {
                format!("apply: automatic island bootstrap into {}", root.display())
            }];

            for key in requested {
                let island = manifest
                    .islands
                    .iter()
                    .find(|island| island.key == key)
                    .ok_or_else(|| format!("unknown island: {key}"))?;
                let entry = island.platforms.iter().find(|entry| entry.target == target);
                match entry {
                    Some(entry) if entry.provider == "embedded" => {
                        rows.push(format!(
                            "embedded {} {}: available with the my-lisp distribution",
                            island.key, island.runtime_version
                        ));
                    }
                    Some(entry) if matches!(entry.provider.as_str(), "apt" | "winget") && !dry_run => {
                        rows.push(install_system_package(island, entry)?);
                    }
                    Some(entry) if matches!(entry.provider.as_str(), "apt" | "winget") => rows.push(format!(
                        "install {} via {} package {}",
                        island.key,
                        entry.provider,
                        entry.package.as_deref().unwrap_or("unknown")
                    )),
                    Some(entry) if entry.provider == "release-asset" && !dry_run => {
                        rows.push(install_release_asset(island, entry, &root)?);
                    }
                    Some(entry) if entry.provider == "release-asset" => rows.push(format!(
                        "download + verify + install {} {}",
                        island.key, island.runtime_version
                    )),
                    Some(entry) if entry.provider == "unsupported" => {
                        return Err(format!(
                            "{} is unsupported on {}: {}",
                            island.key,
                            target,
                            entry.reason.as_deref().unwrap_or("not supplied")
                        ));
                    }
                    Some(entry) => {
                        return Err(format!(
                            "unsupported installer provider {} for {}",
                            entry.provider, island.key
                        ));
                    }
                    None => {
                        return Err(format!(
                            "{} has no manifest entry for target {}",
                            island.key, target
                        ));
                    }
                }
            }
            Ok(rows.join("\n"))
        }
        "status" => {
            let mut rows = Vec::new();
            for island in manifest.islands {
                let entry = island.platforms.iter().find(|entry| entry.target == target);
                let Some(entry) = entry else {
                    rows.push(format!("{}: unsupported", island.key));
                    continue;
                };

                if entry.provider == "unsupported" {
                    rows.push(format!("{}: unsupported", island.key));
                    continue;
                }
                if entry.provider == "embedded" {
                    rows.push(format!(
                        "{} {} {} {}: available (embedded)",
                        island.key, island.runtime_version, target, island.provenance
                    ));
                    continue;
                }

                let probe = interpolate_command(
                    &entry.probe,
                    &root
                        .join(&island.key)
                        .join(&island.runtime_version)
                        .join(target),
                );
                let status = if probe.is_empty() {
                    "absent"
                } else {
                    bounded_probe(&probe, entry.probe_expect.as_deref())
                };
                rows.push(format!(
                    "{} {} {} {}: {}",
                    island.key, island.runtime_version, target, island.provenance, status
                ));
            }
            Ok(rows.join("\n"))
        }
        _ => Err(format!("unknown islands command: {command}")),
    }
}
