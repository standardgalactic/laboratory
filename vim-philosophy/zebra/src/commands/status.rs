use anyhow::Result;

use crate::commands::load_project;
use crate::model::Workflow;
use crate::store::Store;

pub fn run() -> Result<()> {
    let (root, config, tasks) = load_project()?;
    let store = Store::open(&root)?;
    let workflow = Workflow::load(&root.join("workflows").join(format!("{}.yml", config.project.workflow)))?;

    println!("Project: {}  (workflow: {})", config.project.name, config.project.workflow);
    println!();
    for step in &workflow.steps {
        let task = match tasks.get(step) {
            Ok(t) => t,
            Err(_) => {
                println!("  ?  {step:<14} (no task definition found)");
                continue;
            }
        };
        let done = task
            .outputs
            .iter()
            .all(|o| store.current_artifact_id(o).is_some());
        let mark = if done { "done" } else { "pending" };
        let outputs_state: Vec<String> = task
            .outputs
            .iter()
            .map(|o| match store.current_artifact_id(o) {
                Some(id) => format!("{o}={id}"),
                None => format!("{o}=-"),
            })
            .collect();
        println!("  [{mark:<7}] {:<10} {}", task.name, outputs_state.join(" "));
    }
    Ok(())
}
