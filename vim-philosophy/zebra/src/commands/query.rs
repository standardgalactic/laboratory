use anyhow::Result;

use crate::commands::load_project;
use crate::journal::Journal;

pub fn run(filters: &[String]) -> Result<()> {
    let (root, _config, _tasks) = load_project()?;
    let journal = Journal::open(&root.join("journal"))?;
    let events = journal.read_all()?;

    let parsed: Vec<(String, String)> = filters
        .iter()
        .filter_map(|f| f.split_once('=').map(|(k, v)| (k.to_string(), v.to_string())))
        .collect();

    let mut count = 0;
    for ev in events {
        let matches = parsed.iter().all(|(k, v)| match k.as_str() {
            "task" => ev.task.as_deref() == Some(v.as_str()),
            "model" => ev.model.as_deref() == Some(v.as_str()),
            "run" => ev.run.as_deref() == Some(v.as_str()),
            "event" => format!("{:?}", ev.event).to_lowercase() == v.to_lowercase(),
            _ => false,
        });
        if matches {
            count += 1;
            println!(
                "{}  {}  task={:<10} model={:<20} artifacts=[{}]",
                ev.id,
                ev.time.to_rfc3339(),
                ev.task.unwrap_or_default(),
                ev.model.unwrap_or_default(),
                ev.artifacts.join(","),
            );
        }
    }
    println!("({count} matching events)");
    Ok(())
}
