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
            let requested: Vec<String> = if let Ok(keys) = value_after(args, "--with") {
                keys.split(',').filter(|key| !key.is_empty()).map(str::to_string).collect()
            } else {
                let profile_key = value_after(args, "--profile")?;
                manifest.profiles.iter().find(|profile| profile.key == profile_key)
                    .ok_or_else(|| format!("unknown island profile: {profile_key}"))?
                    .islands.clone()
            };
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
        "status" => Ok(manifest.islands.into_iter().map(|island| {
            let outcome = island.platforms.iter().any(|entry| entry.target == target && entry.provider != "unsupported");
            format!("{}: {}", island.key, if outcome { "absent" } else { "unsupported" })
        }).collect::<Vec<_>>().join("\n")),
        _ => Err(format!("unknown islands command: {command}")),
    }
}
