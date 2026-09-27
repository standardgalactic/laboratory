use anyhow::{Context, Result};

use crate::backend;
use crate::commands::load_project;
use crate::context;
use crate::journal::{next_run_id, EventKind, Journal, JournalEvent};
use crate::model::TaskSet;
use crate::store::Store;

pub fn run(task_name: &str, force: bool) -> Result<()> {
    let (root, config, tasks) = load_project()?;
    let store = Store::open(&root)?;
    let journal = Journal::open(&root.join("journal"))?;

    let order = tasks
        .build_order(task_name)
        .with_context(|| format!("resolving dependencies for '{task_name}'"))?;

    for name in order {
        run_one(&root, &config, &tasks, &store, &journal, &name, force)?;
    }
    Ok(())
}

fn run_one(
    root: &std::path::Path,
    config: &crate::model::Config,
    tasks: &TaskSet,
    store: &Store,
    journal: &Journal,
    name: &str,
    force: bool,
) -> Result<()> {
    let task = tasks.get(name)?;

    let already_done = task.outputs.iter().all(|o| store.current_artifact_id(o).is_some());
    if already_done && !force {
        println!("[zebra] {name}: already satisfied ({}), skipping (use --force to re-run)",
            task.outputs.iter()
                .map(|o| store.current_artifact_id(o).unwrap_or_default())
                .collect::<Vec<_>>()
                .join(", "));
        return Ok(());
    }

    let assembled = context::assemble(root, task, store)
        .with_context(|| format!("assembling context for task '{name}'"))?;

    let model = config.model_for(&task.backend).to_string();
    println!("[zebra] {name}: running ({model}) inputs=[{}]", task.inputs.join(", "));

    let events = journal.read_all()?;
    let run_id = next_run_id(&events);

    let result = backend::run(&config.backend.runner, &model, &assembled.full_prompt, config.backend.timeout_secs);

    let result = match result {
        Ok(r) => r,
        Err(e) => {
            journal.append(JournalEvent {
                id: String::new(),
                time: chrono::Utc::now(),
                event: EventKind::TaskFailed,
                run: Some(run_id.clone()),
                task: Some(name.to_string()),
                artifacts: vec![],
                prompt: Some(task.prompt.clone()),
                prompt_hash: Some(assembled.prompt_hash.clone()),
                context_hash: Some(assembled.context_hash.clone()),
                model: Some(model.clone()),
                duration_secs: None,
                note: Some(format!("{e:#}")),
            })?;
            return Err(e).with_context(|| format!("running backend for task '{name}'"));
        }
    };

    let mut artifact_ids = Vec::new();
    for output in &task.outputs {
        let id = store.next_artifact_id()?;
        store.write_artifact(&id, &result.output)?;
        store.set_current(output, &id)?;
        artifact_ids.push(id);
    }

    journal.append(JournalEvent {
        id: String::new(),
        time: chrono::Utc::now(),
        event: EventKind::TaskFinished,
        run: Some(run_id),
        task: Some(name.to_string()),
        artifacts: artifact_ids.clone(),
        prompt: Some(task.prompt.clone()),
        prompt_hash: Some(assembled.prompt_hash.clone()),
        context_hash: Some(assembled.context_hash.clone()),
        model: Some(model.clone()),
        duration_secs: Some(result.duration_secs),
        note: if result.used_mock { Some("mock backend".to_string()) } else { None },
    })?;

    println!(
        "[zebra] {name}: wrote {} in {:.2}s{}",
        artifact_ids.join(", "),
        result.duration_secs,
        if result.used_mock { "  (mock)" } else { "" }
    );

    Ok(())
}
