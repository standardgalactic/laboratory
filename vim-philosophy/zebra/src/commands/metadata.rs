use anyhow::Result;
use serde_json::json;

use crate::commands::load_project;
use crate::journal::Journal;
use crate::store::Store;

pub fn run() -> Result<()> {
    let (root, config, tasks) = load_project()?;
    let store = Store::open(&root)?;
    let journal = Journal::open(&root.join("journal"))?;
    let events = journal.read_all()?;

    let tasks_total = tasks.by_name.len();
    let tasks_done = tasks
        .by_name
        .values()
        .filter(|t| t.outputs.iter().all(|o| store.current_artifact_id(o).is_some()))
        .count();

    let artifacts_count = std::fs::read_dir(root.join("artifacts"))?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map(|x| x == "md").unwrap_or(false))
        .count();

    let out = json!({
        "project": config.project.name,
        "workflow": config.project.workflow,
        "generator_model": config.backend.generator_model,
        "reviewer_model": config.backend.reviewer_model,
        "runner": config.backend.runner,
        "tasks_total": tasks_total,
        "tasks_done": tasks_done,
        "artifacts": artifacts_count,
        "journal_events": events.len(),
    });
    println!("{}", serde_json::to_string_pretty(&out)?);
    Ok(())
}
