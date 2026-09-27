mod backend;
mod commands;
mod context;
mod graph;
mod journal;
mod model;
mod scaffold;
mod store;

use anyhow::Result;
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "zebra", version, about = "An event-sourced graph engine for reproducible document generation")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Scaffold a new Zebra project
    New { name: String },
    /// Show workflow progress for the current project
    Status,
    /// Run a task (and any not-yet-satisfied dependencies)
    Run {
        task: String,
        /// Re-run even if a current artifact already exists for this task's outputs
        #[arg(long)]
        force: bool,
    },
    /// Print machine-readable project metadata as JSON
    Metadata,
    /// Show what depends on a task/output, downstream
    Trace { name: String },
    /// Show what a task/output depends on, upstream
    Why { name: String },
    /// Show the direct inputs a task loads and where they come from
    Inspect { task: String },
    /// List journal events
    Journal {
        #[arg(long)]
        task: Option<String>,
    },
    /// Filter journal events by field=value pairs
    Query {
        /// e.g. task=draft model=granite4.1:8b
        filters: Vec<String>,
    },
    /// Check that current/ pointers resolve to real artifacts
    Verify,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::New { name } => commands::new::run(&name),
        Commands::Status => commands::status::run(),
        Commands::Run { task, force } => commands::run_task::run(&task, force),
        Commands::Metadata => commands::metadata::run(),
        Commands::Trace { name } => commands::trace::run(&name, true),
        Commands::Why { name } => commands::trace::run(&name, false),
        Commands::Inspect { task } => commands::inspect::run(&task),
        Commands::Journal { task } => commands::journal_cmd::run(task.as_deref()),
        Commands::Query { filters } => commands::query::run(&filters),
        Commands::Verify => commands::verify::run(),
    }
}
