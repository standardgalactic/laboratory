use anyhow::Result;

use crate::commands::load_project;
use crate::store::Store;

pub fn run() -> Result<()> {
    let (root, _config, tasks) = load_project()?;
    let store = Store::open(&root)?;

    let mut problems = 0;
    for task in tasks.by_name.values() {
        for output in &task.outputs {
            match store.current_artifact_id(output) {
                Some(id) => {
                    let p = store.artifact_path(&id);
                    if !p.exists() {
                        println!("BROKEN: current/{output}.md points to missing artifact {id}");
                        problems += 1;
                    }
                }
                None => {
                    // Not produced yet — not a problem, just incomplete.
                }
            }
        }
    }

    if problems == 0 {
        println!("OK: all current/ pointers resolve to existing artifacts");
    } else {
        println!("{problems} problem(s) found");
    }
    Ok(())
}
