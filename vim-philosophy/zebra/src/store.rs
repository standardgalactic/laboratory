use anyhow::{Context, Result};
use std::fs;
use std::os::unix::fs as unix_fs;
use std::path::{Path, PathBuf};

/// Artifacts are content, never edited in place: artifacts/A0000001.md,
/// artifacts/A0000002.md, ... "current" state is just a named pointer
/// (a symlink) into that immutable store, exactly like a Git ref.
pub struct Store {
    artifacts_dir: PathBuf,
    current_dir: PathBuf,
}

impl Store {
    pub fn open(root: &Path) -> Result<Store> {
        let artifacts_dir = root.join("artifacts");
        let current_dir = root.join("current");
        fs::create_dir_all(&artifacts_dir)?;
        fs::create_dir_all(&current_dir)?;
        Ok(Store { artifacts_dir, current_dir })
    }

    pub fn next_artifact_id(&self) -> Result<String> {
        let mut max = 0u64;
        for entry in fs::read_dir(&self.artifacts_dir)
            .with_context(|| format!("reading artifacts dir {}", self.artifacts_dir.display()))?
        {
            let entry = entry?;
            let stem = entry.path();
            let stem = stem.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
            if let Some(rest) = stem.strip_prefix('A') {
                if let Ok(n) = rest.parse::<u64>() {
                    max = max.max(n);
                }
            }
        }
        Ok(format!("A{:07}", max + 1))
    }

    /// Write new immutable artifact content, return its id and path.
    pub fn write_artifact(&self, id: &str, content: &str) -> Result<PathBuf> {
        let path = self.artifacts_dir.join(format!("{id}.md"));
        if path.exists() {
            anyhow::bail!("refusing to overwrite existing immutable artifact {}", path.display());
        }
        fs::write(&path, content).with_context(|| format!("writing artifact {}", path.display()))?;
        Ok(path)
    }

    pub fn artifact_path(&self, id: &str) -> PathBuf {
        self.artifacts_dir.join(format!("{id}.md"))
    }

    pub fn artifact_content(&self, id: &str) -> Result<String> {
        let p = self.artifact_path(id);
        fs::read_to_string(&p).with_context(|| format!("reading artifact {}", p.display()))
    }

    /// Point current/<output_name>.md at the given artifact id, replacing
    /// any prior pointer. This is the only mutable state in the project —
    /// and even it is fully derivable from the journal (it's just "latest").
    pub fn set_current(&self, output_name: &str, artifact_id: &str) -> Result<()> {
        let link_path = self.current_dir.join(format!("{output_name}.md"));
        if link_path.exists() || link_path.symlink_metadata().is_ok() {
            fs::remove_file(&link_path).ok();
        }
        let target = PathBuf::from("..").join("artifacts").join(format!("{artifact_id}.md"));
        match unix_fs::symlink(&target, &link_path) {
            Ok(_) => Ok(()),
            Err(_) => {
                // Fall back to a plain copy if symlinks aren't available
                // (e.g. some filesystems under WSL).
                let content = self.artifact_content(artifact_id)?;
                fs::write(&link_path, content)?;
                Ok(())
            }
        }
    }

    pub fn current_path(&self, output_name: &str) -> PathBuf {
        self.current_dir.join(format!("{output_name}.md"))
    }

    pub fn read_current(&self, output_name: &str) -> Result<Option<String>> {
        let p = self.current_path(output_name);
        if !p.exists() {
            return Ok(None);
        }
        Ok(Some(fs::read_to_string(&p).with_context(|| format!("reading {}", p.display()))?))
    }

    /// Resolve current/<output_name>.md to the artifact id it points at, if any.
    pub fn current_artifact_id(&self, output_name: &str) -> Option<String> {
        let p = self.current_path(output_name);
        let target = fs::read_link(&p).ok()?;
        let stem = target.file_stem()?.to_str()?.to_string();
        Some(stem)
    }
}
