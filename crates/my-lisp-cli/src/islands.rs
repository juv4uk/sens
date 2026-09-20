use std::fs;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

use serde::Deserialize;

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
    url: Option<String>,
    checksum_algorithm: Option<String>,
    sha256: Option<String>,
    artifact_format: Option<String>,
    entrypoint: Option<String>,
    reason: Option<String>,
    #[serde(default)]
    probe: Vec<String>,
}

fn bounded_probe(command: &[String]) -> &'static str {
    let Some(program) = command.first() else { return "probe-failed" };
    let mut child = match Command::new(program).args(&command[1..]).stdout(Stdio::null()).stderr(Stdio::null()).spawn() {
        Ok(child) => child,
        Err(_) => return "probe-failed",
    };
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        match child.try_wait() {
            Ok(Some(status)) => return if status.success() { "available" } else { "probe-failed" },
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(20)),
            _ => { let _ = child.kill(); let _ = child.wait(); return "probe-failed"; }
        }
    }
}

fn fetch_artifact(url: &str, temporary: &std::path::Path) -> Result<(), String> {
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
            "60",
            "--output",
            &output,
            url,
        ])
        .status()
    {
        Ok(status) if status.success() => Ok(()),
        Ok(status) => {
            Err(format!("download failed for {url}: curl exit {}", status))
        }
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
                .map_err(|error| format!("download failed for {url}: curl unavailable ({curl_error}); powershell failed: {error}"))?;
            if status.success() {
                return Ok(());
            }
            Err(format!("download failed for {url}: powershell exit {status}"))
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

fn value_after<'a>(args: &'a [String], option: &str) -> Result<&'a str, String> {
    args.iter()
        .position(|arg| arg == option)
        .and_then(|index| args.get(index + 1))
        .map(String::as_str)
        .ok_or_else(|| format!("{option} requires a value"))
}

fn load_manifest(path: &str) -> Result<Manifest, String> {
    let source = fs::read_to_string(path).map_err(|error| format!("cannot read manifest {path}: {error}"))?;
    let manifest: Manifest = serde_json::from_str(&source)
        .map_err(|error| format!("invalid manifest {path}: {error}"))?;
    if manifest.protocol != "my-lisp-islands-manifest/1" {
        return Err(format!("unsupported manifest protocol: {}", manifest.protocol));
    }
    let known_targets = ["linux-x86_64", "windows-x86_64", "macos-x86_64", "macos-aarch64"];
    let known_providers = ["apt", "dnf", "brew", "winget", "release-asset", "unsupported"];
    let mut island_keys = std::collections::HashSet::new();
    let mut install_keys = std::collections::HashSet::new();
    for island in &manifest.islands {
        if island.key.is_empty() || !island_keys.insert(&island.key) {
            return Err(format!("manifest has duplicate or empty island key: {}", island.key));
        }
        if island.runtime_version.is_empty()
            || island.abi_compatibility.is_empty()
            || island.install_key.is_empty()
            || island.license.is_empty()
            || island.provenance.is_empty()
        {
            return Err(format!("island {} is missing required release metadata", island.key));
        }
        if !install_keys.insert(&island.install_key) {
            return Err(format!("manifest has duplicate install key: {}", island.install_key));
        }

        let mut targets = std::collections::HashSet::new();
        for entry in &island.platforms {
            if !targets.insert(&entry.target) {
                return Err(format!("island {} has duplicate target {}", island.key, entry.target));
            }
            if !known_targets.contains(&entry.target.as_str()) {
                return Err(format!("island {} has unsupported target {}", island.key, entry.target));
            }
            if !known_providers.contains(&entry.provider.as_str()) {
                return Err(format!("island {} has unsupported provider {}", island.key, entry.provider));
            }

            match entry.provider.as_str() {
                "release-asset" => {
                    let url = entry.url.as_deref().ok_or_else(|| {
                        format!("island {} release asset is missing URL", island.key)
                    })?;
                    if !(url.starts_with("https://") || url.starts_with("http://") || url.starts_with("file://")) {
                        return Err(format!("island {} release asset has unsupported URL", island.key));
                    }
                    if entry.checksum_algorithm.as_deref() != Some("sha256") {
                        return Err(format!("island {} release asset must declare sha256 checksum algorithm", island.key));
                    }
                    let sha256 = entry.sha256.as_deref().ok_or_else(|| {
                        format!("island {} release asset is missing SHA-256", island.key)
                    })?;
                    if sha256.len() != 64 || !sha256.bytes().all(|byte| byte.is_ascii_hexdigit()) {
                        return Err(format!("island {} has invalid SHA-256", island.key));
                    }
                    if entry.artifact_format.as_deref().is_none_or(str::is_empty) {
                        return Err(format!("island {} release asset is missing artifact format", island.key));
                    }
                    if entry.entrypoint.as_deref().is_none_or(str::is_empty) {
                        return Err(format!("island {} release asset is missing entrypoint", island.key));
                    }
                    if entry.probe.is_empty() {
                        return Err(format!("island {} release asset is missing a bounded probe", island.key));
                    }
                }
                "unsupported" => {
                    if entry.reason.as_deref().is_none_or(str::is_empty) {
                        return Err(format!("island {} unsupported target is missing reason", island.key));
                    }
                }
                _ => {
                    if entry.package.as_deref().is_none_or(str::is_empty) {
                        return Err(format!("island {} package provider is missing package name", island.key));
                    }
                    if entry.entrypoint.as_deref().is_none_or(str::is_empty) {
                        return Err(format!("island {} package provider is missing entrypoint", island.key));
                    }
                    if entry.probe.is_empty() {
                        return Err(format!("island {} package provider is missing a bounded probe", island.key));
                    }
                }
            }
        }
    }
    Ok(manifest)
}

fn requested_keys(manifest: &Manifest, args: &[String]) -> Result<Vec<String>, String> {
    if let Ok(keys) = value_after(args, "--with") {
        return Ok(keys.split(',').filter(|key| !key.is_empty()).map(str::to_string).collect());
    }
    let profile_key = value_after(args, "--profile")?;
    manifest.profiles.iter().find(|profile| profile.key == profile_key)
        .map(|profile| profile.islands.clone())
        .ok_or_else(|| format!("unknown island profile: {profile_key}"))
}

pub fn run(args: &[String]) -> Result<String, String> {
    let Some(command) = args.first().map(String::as_str) else {
        return Err("usage: islands plan|status --manifest <path> [--with key,...]".to_string());
    };
    let manifest = load_manifest(value_after(args, "--manifest")?)?;
    let target = args
        .iter()
        .position(|arg| arg == "--target")
        .and_then(|index| args.get(index + 1))
        .map(String::as_str)
        .unwrap_or(current_target());
    match command {
        "plan" => {
            let requested = requested_keys(&manifest, args)?;
            let mut rows = Vec::new();
            for key in requested {
                let island = manifest.islands.iter().find(|island| island.key == key)
                    .ok_or_else(|| format!("unknown island: {key}"))?;
                let entry = island.platforms.iter().find(|entry| entry.target == target);
                let install_root = args
                    .iter()
                    .position(|arg| arg == "--root")
                    .and_then(|index| args.get(index + 1))
                    .map(String::as_str);
                let destination = install_root.map(|root| {
                    std::path::Path::new(root)
                        .join(&island.install_key)
                        .join(&island.runtime_version)
                        .join(target)
                });
                let verified_installed = destination
                    .as_ref()
                    .map(|path| path.join("runtime.bin").is_file());
                let mut row = format!(
                    "island: {}\nversion: {}\nabi: {}\ninstall-key: {}\nlicense: {}\nlicense-acceptance: {}\nprovenance: {}\ntarget: {}",
                    island.key,
                    island.runtime_version,
                    island.abi_compatibility,
                    island.install_key,
                    island.license,
                    if island.license_acceptance_required { "required" } else { "not-required" },
                    island.provenance,
                    target
                );
                match (&destination, verified_installed) {
                    (Some(path), Some(installed)) => {
                        row.push_str(&format!(
                            "\ndestination: {}\nverified-installed: {}",
                            path.display(),
                            if installed { "yes" } else { "no" }
                        ));
                    }
                    _ => row.push_str("\ndestination: <supply --root>\nverified-installed: unknown"),
                }
                match entry {
                    Some(entry) if entry.provider == "unsupported" => {
                        row.push_str(&format!("\noutcome: unsupported\nreason: {}", entry.reason.as_deref().unwrap_or("not supplied")));
                    }
                    Some(entry) => {
                        row.push_str(&format!("\nprovider: {}\noutcome: installable", entry.provider));
                        if let Some(package) = &entry.package { row.push_str(&format!("\npackage: {package}")); }
                        if let Some(url) = &entry.url { row.push_str(&format!("\nurl: {url}")); }
                        if let Some(algorithm) = &entry.checksum_algorithm { row.push_str(&format!("\nchecksum-algorithm: {algorithm}")); }
                        if let Some(sha256) = &entry.sha256 { row.push_str(&format!("\nsha256:{sha256}")); }
                        if let Some(format) = &entry.artifact_format { row.push_str(&format!("\nartifact-format: {format}")); }
                        if let Some(entrypoint) = &entry.entrypoint { row.push_str(&format!("\nentrypoint: {entrypoint}")); }
                    }
                    None => row.push_str("\noutcome: unsupported\nreason: manifest has no entry for this target"),
                }
                rows.push(row);
            }
            Ok(rows.join("\n---\n"))
        }
        "install" => {
            let root = value_after(args, "--root")?;
            let apply = args.iter().any(|arg| arg == "--apply");
            let dry_run = args.iter().any(|arg| arg == "--dry-run");
            if !apply && !dry_run { return Err("install requires --dry-run or --apply".to_string()); }
            let mut rows = vec!["dry-run: no files will be created".to_string()];
            if apply { rows[0] = "apply: verified artifacts will be published".to_string(); }
            for key in requested_keys(&manifest, args)? {
                let island = manifest.islands.iter().find(|island| island.key == key)
                    .ok_or_else(|| format!("unknown island: {key}"))?;
                let entry = island.platforms.iter().find(|entry| entry.target == target);
                match entry {
                    Some(entry) if entry.provider == "release-asset" && apply => {
                        let url = entry.url.as_deref().ok_or_else(|| format!("release asset {} has no URL", island.key))?;
                        let expected = entry.sha256.as_deref().ok_or_else(|| format!("release asset {} has no SHA-256", island.key))?;
                        let target_dir = std::path::Path::new(root).join(&island.key).join(&island.runtime_version).join(target);
                        let runtime = target_dir.join("runtime.bin");
                        if runtime.is_file() {
                            let existing = fs::read(&runtime).map_err(|error| error.to_string())?;
                            let existing_digest = my_lisp::sha256_source(&existing).iter().map(|byte| format!("{byte:02x}")).collect::<String>();
                            if existing_digest != expected {
                                return Err(format!("existing installation checksum mismatch for {}", island.key));
                            }
                            rows.push(format!("already installed {}", target_dir.display()));
                            continue;
                        }
                        let temporary = std::path::PathBuf::from(format!("{}.tmp-{}", target_dir.display(), std::process::id()));
                        if temporary.exists() { let _ = fs::remove_file(&temporary); }
                        fs::create_dir_all(target_dir.parent().ok_or_else(|| "invalid install target".to_string())?).map_err(|error| error.to_string())?;
                        if let Err(error) = fetch_artifact(url, &temporary) {
                            let _ = fs::remove_file(&temporary);
                            return Err(error);
                        }
                        let bytes = fs::read(&temporary).map_err(|error| error.to_string())?;
                        let actual = my_lisp::sha256_source(&bytes).iter().map(|byte| format!("{byte:02x}")).collect::<String>();
                        if actual != expected { let _ = fs::remove_file(&temporary); return Err(format!("checksum mismatch for {}", island.key)); }
                        let staging = target_dir.with_extension(format!("stage-{}", std::process::id()));
                        if staging.exists() { let _ = fs::remove_dir_all(&staging); }
                        fs::create_dir_all(&staging).map_err(|error| error.to_string())?;
                        fs::rename(&temporary, staging.join("runtime.bin")).map_err(|error| error.to_string())?;
                        fs::rename(&staging, &target_dir).map_err(|error| error.to_string())?;
                        let probe = bounded_probe(&entry.probe);
                        rows.push(format!("published {}: {probe}", target_dir.display()));
                    }
                    Some(entry) if entry.provider != "unsupported" => rows.push(format!(
                        "install {}", std::path::Path::new(root).join(&island.key).join(&island.runtime_version).join(target).display()
                    )),
                    Some(entry) => rows.push(format!("skip {}: unsupported ({})", island.key, entry.reason.as_deref().unwrap_or("not supplied"))),
                    None => rows.push(format!("skip {}: unsupported target {target}", island.key)),
                }
            }
            Ok(rows.join("\n"))
        }
        "status" => {
            let root = args.iter().position(|arg| arg == "--root")
                .and_then(|index| args.get(index + 1)).map(String::as_str);
            Ok(manifest.islands.into_iter().map(|island| {
            let entry = island.platforms.iter().find(|entry| entry.target == target);
            let Some(entry) = entry else { return format!("{}: unsupported", island.key) };
            if entry.provider == "unsupported" { return format!("{}: unsupported", island.key); }
            let artifact = root.map(|base| std::path::Path::new(base).join(&island.key).join(&island.runtime_version).join(target).join("runtime.bin"));
            let status = if let Some(_path) = artifact.filter(|path| path.is_file()) {
                if entry.probe.is_empty() { "available" } else { bounded_probe(&entry.probe) }
            } else { "absent" };
            format!("{} {} {} {}: {}", island.key, island.runtime_version, target, island.provenance, status)
        }).collect::<Vec<_>>().join("\n"))
        }
        _ => Err(format!("unknown islands command: {command}")),
    }
}
