use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

/// One immutable record in the journal. Zebra never rewrites project state
/// in place — every run, rollback, or note is appended here, and the graph
/// of tasks/artifacts is reconstructed by folding over these events.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JournalEvent {
    pub id: String, // E0000001
    pub time: DateTime<Utc>,
    pub event: EventKind,
    pub run: Option<String>,       // R0000001
    pub task: Option<String>,      // task name
    pub artifacts: Vec<String>,    // artifact ids produced, if any
    pub prompt: Option<String>,    // prompt name
    pub prompt_hash: Option<String>,
    pub context_hash: Option<String>,
    pub model: Option<String>,
    pub duration_secs: Option<f64>,
    #[serde(default)]
    pub note: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub enum EventKind {
    TaskStarted,
    TaskFinished,
    TaskFailed,
    Rollback,
    Note,
}

pub struct Journal {
    dir: PathBuf,
}

impl Journal {
    pub fn open(dir: &Path) -> Result<Journal> {
        fs::create_dir_all(dir).with_context(|| format!("creating journal dir {}", dir.display()))?;
        Ok(Journal { dir: dir.to_path_buf() })
    }

    fn entries(&self) -> Result<Vec<PathBuf>> {
        let mut v: Vec<PathBuf> = fs::read_dir(&self.dir)
            .with_context(|| format!("reading journal dir {}", self.dir.display()))?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().map(|e| e == "yaml").unwrap_or(false))
            .collect();
        v.sort();
        Ok(v)
    }

    pub fn read_all(&self) -> Result<Vec<JournalEvent>> {
        let mut out = Vec::new();
        for p in self.entries()? {
            let text = fs::read_to_string(&p)
                .with_context(|| format!("reading journal entry {}", p.display()))?;
            let ev: JournalEvent = serde_yaml::from_str(&text)
                .with_context(|| format!("parsing journal entry {}", p.display()))?;
            out.push(ev);
        }
        Ok(out)
    }

    /// Next sequence number, 1-based, derived from how many entries exist.
    pub fn next_seq(&self) -> Result<u64> {
        Ok(self.entries()?.len() as u64 + 1)
    }

    pub fn append(&self, mut ev: JournalEvent) -> Result<()> {
        let seq = self.next_seq()?;
        ev.id = format!("E{:07}", seq);
        let path = self.dir.join(format!("{:07}.yaml", seq));
        let text = serde_yaml::to_string(&ev)?;
        fs::write(&path, text).with_context(|| format!("writing journal entry {}", path.display()))?;
        Ok(())
    }
}

/// Allocate the next run id by counting how many task-started/finished
/// events already reference a run. Simple monotonic counter reconstructed
/// from the journal rather than stored anywhere mutable.
pub fn next_run_id(events: &[JournalEvent]) -> String {
    let mut max = 0u64;
    for e in events {
        if let Some(r) = &e.run {
            if let Ok(n) = r.trim_start_matches('R').parse::<u64>() {
                max = max.max(n);
            }
        }
    }
    format!("R{:07}", max + 1)
}
