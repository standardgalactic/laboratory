use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

/// A declarative task definition, loaded from tasks/<name>.yaml.
/// A task is a build rule: given some inputs, run a backend against a
/// prompt, and produce named outputs. Nothing here is imperative code —
/// the engine (see `commands::run`) interprets this data.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub name: String,
    #[serde(default)]
    pub description: String,
    /// Names that are either the literal string "project" (meaning
    /// project.md) or the `outputs` name of some other task.
    #[serde(default)]
    pub inputs: Vec<String>,
    /// Named outputs this task produces. Usually one.
    pub outputs: Vec<String>,
    /// Which model role to use: a key into config.backend (e.g. "generator",
    /// "reviewer").
    #[serde(default = "default_backend_role")]
    pub backend: String,
    /// Name of the prompt file (without .md) under prompts/.
    pub prompt: String,
}

fn default_backend_role() -> String {
    "generator".to_string()
}

impl Task {
    pub fn load(path: &Path) -> Result<Task> {
        let text = fs::read_to_string(path)
            .with_context(|| format!("reading task file {}", path.display()))?;
        let task: Task = serde_yaml::from_str(&text)
            .with_context(|| format!("parsing task file {}", path.display()))?;
        Ok(task)
    }
}

/// The full set of tasks known to a project, indexed by name and by the
/// output they produce. This is the static half of the graph: which nodes
/// (tasks) exist and what edges (inputs/outputs) connect them. The dynamic
/// half — which artifacts actually exist — is reconstructed from the
/// journal (see `journal.rs`).
#[derive(Debug, Default)]
pub struct TaskSet {
    pub by_name: HashMap<String, Task>,
    /// output name -> producing task name
    pub producer_of: HashMap<String, String>,
}

impl TaskSet {
    pub fn load(tasks_dir: &Path) -> Result<TaskSet> {
        let mut set = TaskSet::default();
        if !tasks_dir.exists() {
            return Ok(set);
        }
        let mut entries: Vec<PathBuf> = fs::read_dir(tasks_dir)
            .with_context(|| format!("reading tasks dir {}", tasks_dir.display()))?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| {
                p.extension()
                    .map(|e| e == "yaml" || e == "yml")
                    .unwrap_or(false)
            })
            .collect();
        entries.sort();
        for path in entries {
            let task = Task::load(&path)?;
            for out in &task.outputs {
                set.producer_of.insert(out.clone(), task.name.clone());
            }
            set.by_name.insert(task.name.clone(), task);
        }
        Ok(set)
    }

    pub fn get(&self, name: &str) -> Result<&Task> {
        self.by_name
            .get(name)
            .ok_or_else(|| anyhow!("no such task: {name}"))
    }

    /// Direct dependency task names for a given task (derived from inputs).
    pub fn direct_deps(&self, task: &Task) -> Vec<String> {
        task.inputs
            .iter()
            .filter(|i| i.as_str() != "project")
            .filter_map(|i| self.producer_of.get(i).cloned())
            .collect()
    }

    /// Tasks that directly consume `output_or_task`'s output(s) — i.e. the
    /// downstream neighbors, used by `trace`.
    pub fn direct_dependents(&self, name: &str) -> Vec<String> {
        let target_outputs: Vec<String> = match self.by_name.get(name) {
            Some(t) => t.outputs.clone(),
            None => vec![name.to_string()],
        };
        let mut out = Vec::new();
        for t in self.by_name.values() {
            if t.inputs.iter().any(|i| target_outputs.contains(i)) {
                out.push(t.name.clone());
            }
        }
        out.sort();
        out
    }

    /// Topologically ordered list of dependencies needed to run `task_name`,
    /// including the task itself, closest-dependency-first.
    pub fn build_order(&self, task_name: &str) -> Result<Vec<String>> {
        let mut order = Vec::new();
        let mut visiting = Vec::new();
        self.visit(task_name, &mut order, &mut visiting)?;
        Ok(order)
    }

    fn visit(&self, name: &str, order: &mut Vec<String>, visiting: &mut Vec<String>) -> Result<()> {
        if order.contains(&name.to_string()) {
            return Ok(());
        }
        if visiting.contains(&name.to_string()) {
            return Err(anyhow!("dependency cycle detected at task '{name}'"));
        }
        visiting.push(name.to_string());
        let task = self.get(name)?;
        for dep in self.direct_deps(task) {
            self.visit(&dep, order, visiting)?;
        }
        visiting.retain(|n| n != name);
        order.push(name.to_string());
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectConfig {
    pub name: String,
    #[serde(default = "default_workflow")]
    pub workflow: String,
}

fn default_workflow() -> String {
    "default".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendConfig {
    #[serde(default = "default_runner")]
    pub runner: String, // "ollama" | "mock"
    #[serde(default = "default_generator_model")]
    pub generator_model: String,
    #[serde(default = "default_reviewer_model")]
    pub reviewer_model: String,
    #[serde(default = "default_timeout")]
    pub timeout_secs: u64,
}

fn default_runner() -> String {
    "ollama".to_string()
}
fn default_generator_model() -> String {
    "granite4.1:3b".to_string()
}
fn default_reviewer_model() -> String {
    "granite4.1:8b".to_string()
}
fn default_timeout() -> u64 {
    600
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub project: ProjectConfig,
    #[serde(default = "default_backend_config")]
    pub backend: BackendConfig,
}

fn default_backend_config() -> BackendConfig {
    toml::from_str("").unwrap_or(BackendConfig {
        runner: default_runner(),
        generator_model: default_generator_model(),
        reviewer_model: default_reviewer_model(),
        timeout_secs: default_timeout(),
    })
}

impl Config {
    pub fn load(path: &Path) -> Result<Config> {
        let text = fs::read_to_string(path)
            .with_context(|| format!("reading config {}", path.display()))?;
        let cfg: Config = toml::from_str(&text)
            .with_context(|| format!("parsing config {}", path.display()))?;
        Ok(cfg)
    }

    pub fn model_for(&self, backend_role: &str) -> &str {
        match backend_role {
            "reviewer" => &self.backend.reviewer_model,
            _ => &self.backend.generator_model,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Workflow {
    pub steps: Vec<String>,
}

impl Workflow {
    pub fn load(path: &Path) -> Result<Workflow> {
        let text = fs::read_to_string(path)
            .with_context(|| format!("reading workflow {}", path.display()))?;
        let wf: Workflow = serde_yaml::from_str(&text)
            .with_context(|| format!("parsing workflow {}", path.display()))?;
        Ok(wf)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn task(name: &str, inputs: &[&str], outputs: &[&str]) -> Task {
        Task {
            name: name.to_string(),
            description: String::new(),
            inputs: inputs.iter().map(|s| s.to_string()).collect(),
            outputs: outputs.iter().map(|s| s.to_string()).collect(),
            backend: "generator".to_string(),
            prompt: name.to_string(),
        }
    }

    fn linear_set() -> TaskSet {
        let mut set = TaskSet::default();
        for t in [
            task("classify", &["project"], &["classification"]),
            task("analyze", &["project", "classification"], &["analysis"]),
            task("outline", &["analysis"], &["outline"]),
            task("draft", &["outline"], &["draft"]),
        ] {
            for o in &t.outputs {
                set.producer_of.insert(o.clone(), t.name.clone());
            }
            set.by_name.insert(t.name.clone(), t);
        }
        set
    }

    #[test]
    fn build_order_is_topological() {
        let set = linear_set();
        let order = set.build_order("draft").unwrap();
        assert_eq!(order, vec!["classify", "analyze", "outline", "draft"]);
    }

    #[test]
    fn build_order_of_root_task_is_itself() {
        let set = linear_set();
        let order = set.build_order("classify").unwrap();
        assert_eq!(order, vec!["classify"]);
    }

    #[test]
    fn direct_dependents_finds_downstream_consumers() {
        let set = linear_set();
        assert_eq!(set.direct_dependents("classification"), vec!["analyze".to_string()]);
        assert_eq!(set.direct_dependents("analysis"), vec!["outline".to_string()]);
    }

    #[test]
    fn cycle_is_detected() {
        let mut set = TaskSet::default();
        let a = task("a", &["b_out"], &["a_out"]);
        let b = task("b", &["a_out"], &["b_out"]);
        for t in [a, b] {
            for o in &t.outputs {
                set.producer_of.insert(o.clone(), t.name.clone());
            }
            set.by_name.insert(t.name.clone(), t);
        }
        let result = set.build_order("a");
        assert!(result.is_err(), "expected a cycle error, got {result:?}");
    }
}
