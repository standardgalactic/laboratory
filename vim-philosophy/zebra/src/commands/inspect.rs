use anyhow::Result;

use crate::commands::load_project;
use crate::context;
use crate::store::Store;

pub fn run(task_name: &str) -> Result<()> {
    let (root, _config, tasks) = load_project()?;
    let store = Store::open(&root)?;
    let task = tasks.get(task_name)?;

    println!("{task_name}");
    println!("  prompt: prompts/{}.md", task.prompt);
    println!("  backend role: {}", task.backend);
    println!("  outputs: {}", task.outputs.join(", "));
    println!("  inputs:");
    for input in &task.inputs {
        if input == "project" {
            println!("    - project.md");
        } else {
            match store.current_artifact_id(input) {
                Some(id) => println!("    - {input}  (current -> {id})"),
                None => println!("    - {input}  (not yet produced)"),
            }
        }
    }

    match context::assemble(&root, task, &store) {
        Ok(a) => {
            println!();
            println!("  prompt_hash:  {}", a.prompt_hash);
            println!("  context_hash: {}", a.context_hash);
        }
        Err(e) => {
            println!();
            println!("  (cannot assemble yet: {e:#})");
        }
    }
    Ok(())
}
