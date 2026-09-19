use std::fs;

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
    license: String,
    provenance: String,
    platforms: Vec<PlatformEntry>,
}

#[derive(Deserialize)]
struct PlatformEntry {
    target: String,
    provider: String,
    package: Option<String>,
    url: Option<String>,
    sha256: Option<String>,
    reason: Option<String>,
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
                let mut row = format!(
                    "island: {}\nversion: {}\nlicense: {}\nprovenance: {}\ntarget: {}",
                    island.key, island.runtime_version, island.license, island.provenance, target
                );
                match entry {
                    Some(entry) if entry.provider == "unsupported" => {
                        row.push_str(&format!("\noutcome: unsupported\nreason: {}", entry.reason.as_deref().unwrap_or("not supplied")));
                    }
                    Some(entry) => {
                        row.push_str(&format!("\nprovider: {}\noutcome: installable", entry.provider));
                        if let Some(package) = &entry.package { row.push_str(&format!("\npackage: {package}")); }
                        if let Some(url) = &entry.url { row.push_str(&format!("\nurl: {url}")); }
                        if let Some(sha256) = &entry.sha256 { row.push_str(&format!("\nsha256:{sha256}")); }
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
                        let source = url.strip_prefix("file://").ok_or_else(|| "installer v1 supports verified file:// artifacts only".to_string())?;
                        let bytes = fs::read(source).map_err(|error| format!("cannot read artifact {source}: {error}"))?;
                        let actual = my_lisp::sha256_source(&bytes).iter().map(|byte| format!("{byte:02x}")).collect::<String>();
                        let expected = entry.sha256.as_deref().ok_or_else(|| format!("release asset {} has no SHA-256", island.key))?;
                        if actual != expected { return Err(format!("checksum mismatch for {}", island.key)); }
                        let target_dir = std::path::Path::new(root).join(&island.key).join(&island.runtime_version).join(target);
                        let temporary = target_dir.with_extension("tmp");
                        fs::create_dir_all(&temporary).map_err(|error| error.to_string())?;
                        fs::write(temporary.join("runtime.bin"), &bytes).map_err(|error| error.to_string())?;
                        fs::create_dir_all(target_dir.parent().ok_or_else(|| "invalid install target".to_string())?).map_err(|error| error.to_string())?;
                        fs::rename(&temporary, &target_dir).map_err(|error| error.to_string())?;
                        rows.push(format!("installed {}", target_dir.display()));
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
        "status" => Ok(manifest.islands.into_iter().map(|island| {
            let outcome = island.platforms.iter().any(|entry| entry.target == target && entry.provider != "unsupported");
            format!("{}: {}", island.key, if outcome { "absent" } else { "unsupported" })
        }).collect::<Vec<_>>().join("\n")),
        _ => Err(format!("unknown islands command: {command}")),
    }
}
