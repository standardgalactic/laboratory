use anyhow::{Context as _, Result};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

use crate::model::Task;
use crate::store::Store;

pub struct Assembled {
    pub prompt_text: String,
    pub context_text: String,
    pub full_prompt: String,
    pub prompt_hash: String,
    pub context_hash: String,
    pub sources: Vec<String>, // human-readable list of what was loaded, for `inspect`/`why`
}

/// Assemble the prompt + context for a task exactly the way it will be sent
/// to the backend, and record what went into it (for provenance and for
/// `zebra inspect`). Nothing here mutates state — pure read + concatenate.
pub fn assemble(root: &Path, task: &Task, store: &Store) -> Result<Assembled> {
    let prompt_path = root.join("prompts").join(format!("{}.md", task.prompt));
    let prompt_text = fs::read_to_string(&prompt_path)
        .with_context(|| format!("reading prompt {}", prompt_path.display()))?;

    let mut context_text = String::new();
    let mut sources = Vec::new();

    for input in &task.inputs {
        if input == "project" {
            let p = root.join("project.md");
            if p.exists() {
                let text = fs::read_to_string(&p)?;
                context_text.push_str(&format!("\n# INPUT: project\n\n{text}\n"));
                sources.push("project.md".to_string());
            }
            continue;
        }
        match store.read_current(input)? {
            Some(text) => {
                context_text.push_str(&format!("\n# INPUT: {input}\n\n{text}\n"));
                sources.push(format!("current/{input}.md"));
            }
            None => {
                anyhow::bail!(
                    "task '{}' needs input '{input}' but no artifact has been produced for it yet",
                    task.name
                );
            }
        }
    }

    let full_prompt = format!("{prompt_text}\n\n{context_text}");

    Ok(Assembled {
        prompt_hash: hash(&prompt_text),
        context_hash: hash(&context_text),
        full_prompt,
        prompt_text,
        context_text,
        sources,
    })
}

pub fn hash(text: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    hex::encode(hasher.finalize())
}
