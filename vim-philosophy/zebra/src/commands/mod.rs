pub mod inspect;
pub mod journal_cmd;
pub mod metadata;
pub mod new;
pub mod query;
pub mod run_task;
pub mod status;
pub mod trace;
pub mod verify;

use anyhow::{Context, Result};
use std::path::PathBuf;

use crate::model::{Config, TaskSet};

/// Locate the project root: the current directory, provided it has a
/// zebra.toml. Zebra deliberately does not walk upward looking for one —
/// a project is wherever you run it, no hidden magic.
pub fn find_root() -> Result<PathBuf> {
    let cwd = std::env::current_dir()?;
    if !cwd.join("zebra.toml").exists() {
        anyhow::bail!(
            "no zebra.toml in {} — run this inside a project created with `zebra new`",
            cwd.display()
        );
    }
    Ok(cwd)
}

pub fn load_project() -> Result<(PathBuf, Config, TaskSet)> {
    let root = find_root()?;
    let config = Config::load(&root.join("zebra.toml")).context("loading zebra.toml")?;
    let tasks = TaskSet::load(&root.join("tasks")).context("loading tasks/")?;
    Ok((root, config, tasks))
}
