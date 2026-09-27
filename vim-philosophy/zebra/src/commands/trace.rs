use anyhow::Result;

use crate::commands::load_project;
use crate::graph;

pub fn run(name: &str, downstream: bool) -> Result<()> {
    let (_root, _config, tasks) = load_project()?;

    let path = if downstream {
        graph::trace_downstream(&tasks, name)
    } else {
        graph::trace_upstream(&tasks, name)
    };

    if path.len() == 1 {
        println!("{name}: nothing {} in the task graph", if downstream { "downstream" } else { "upstream" });
        return Ok(());
    }

    for (depth, node) in path {
        println!("{}{}{node}", "  ".repeat(depth), if depth == 0 { "" } else { "\u{2514}\u{2500} " });
    }
    Ok(())
}
