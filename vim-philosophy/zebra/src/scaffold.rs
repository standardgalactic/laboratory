use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

const DEFAULT_TASKS: &[(&str, &str, &[&str], &[&str], &str)] = &[
    // (name, description, inputs, outputs, backend_role)
    ("classify", "Classify the project's subject matter and target form.", &["project"], &["classification"], "generator"),
    ("analyze", "Analyze source material and constraints.", &["project", "classification"], &["analysis"], "generator"),
    ("outline", "Generate a hierarchical outline.", &["project", "classification", "analysis"], &["outline"], "generator"),
    ("draft", "Produce a full draft from the outline.", &["project", "outline", "analysis"], &["draft"], "generator"),
    ("review", "Critique the draft against project goals.", &["project", "draft"], &["review"], "reviewer"),
    ("revise", "Revise the draft in light of the review.", &["draft", "review"], &["revision"], "generator"),
    ("proof", "Check consistency and terminology.", &["revision"], &["proof"], "reviewer"),
    ("publish", "Produce the final publishable artifact.", &["proof", "revision"], &["publication"], "generator"),
];

pub fn new_project(dir: &Path, name: &str) -> Result<()> {
    for sub in ["tasks", "prompts", "theory", "workflows", "artifacts", "current", "journal"] {
        fs::create_dir_all(dir.join(sub))
            .with_context(|| format!("creating {sub}/"))?;
    }

    fs::write(
        dir.join("zebra.toml"),
        format!(
            "[project]\nname = \"{name}\"\nworkflow = \"default\"\n\n\
             [backend]\nrunner = \"ollama\"\ngenerator_model = \"granite4.1:3b\"\nreviewer_model = \"granite4.1:8b\"\ntimeout_secs = 600\n"
        ),
    )?;

    fs::write(
        dir.join("project.md"),
        format!(
            "# {name}\n\n\
             ## Goal\n\n\
             (What is this project trying to produce?)\n\n\
             ## Audience\n\n\
             (Who is this for?)\n\n\
             ## Theory modules\n\n\
             (Which theory/ files should inform this work, if any?)\n\n\
             ## Constraints\n\n\
             (Length, tone, citation style, anything the drafting stages must respect.)\n\n\
             ## Notes\n\n"
        ),
    )?;

    let mut step_names = Vec::new();
    for (name, desc, inputs, outputs, backend) in DEFAULT_TASKS {
        step_names.push(format!("  - {name}"));
        let inputs_yaml = inputs
            .iter()
            .map(|i| format!("  - {i}"))
            .collect::<Vec<_>>()
            .join("\n");
        let outputs_yaml = outputs
            .iter()
            .map(|o| format!("  - {o}"))
            .collect::<Vec<_>>()
            .join("\n");
        let task_yaml = format!(
            "name: {name}\ndescription: \"{desc}\"\ninputs:\n{inputs_yaml}\noutputs:\n{outputs_yaml}\nbackend: {backend}\nprompt: {name}\n"
        );
        fs::write(dir.join("tasks").join(format!("{name}.yaml")), task_yaml)?;

        let prompt_md = format!(
            "# {name} stage\n\n\
             {desc}\n\n\
             Follow the project's stated goal, audience, and constraints above.\n\
             Write only the {name} artifact itself — no meta-commentary about\n\
             the process, no restating these instructions.\n"
        );
        fs::write(dir.join("prompts").join(format!("{name}.md")), prompt_md)?;
    }

    fs::write(
        dir.join("workflows").join("default.yml"),
        format!("steps:\n{}\n", step_names.join("\n")),
    )?;

    fs::write(
        dir.join("theory").join(".gitkeep"),
        "Theory modules referenced by prompts go here.\n",
    )?;

    Ok(())
}
