use anyhow::Result;

use crate::commands::load_project;
use crate::journal::Journal;

pub fn run(task_filter: Option<&str>) -> Result<()> {
    let (root, _config, _tasks) = load_project()?;
    let journal = Journal::open(&root.join("journal"))?;
    let events = journal.read_all()?;

    for ev in events {
        if let Some(f) = task_filter {
            if ev.task.as_deref() != Some(f) {
                continue;
            }
        }
        println!(
            "{}  {}  {:<14}  task={:<10} run={:<10} artifacts=[{}]{}",
            ev.id,
            ev.time.to_rfc3339(),
            format!("{:?}", ev.event),
            ev.task.unwrap_or_default(),
            ev.run.unwrap_or_default(),
            ev.artifacts.join(","),
            ev.note.map(|n| format!("  note={n}")).unwrap_or_default(),
        );
    }
    Ok(())
}
