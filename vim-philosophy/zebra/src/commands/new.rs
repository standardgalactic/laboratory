use anyhow::{Context, Result};
use std::path::Path;

use crate::scaffold;

pub fn run(name: &str) -> Result<()> {
    let dir = Path::new(name);
    if dir.exists() {
        anyhow::bail!("{} already exists", dir.display());
    }
    std::fs::create_dir_all(dir).with_context(|| format!("creating {}", dir.display()))?;
    scaffold::new_project(dir, name)?;
    println!("Created project '{name}' in {}/", dir.display());
    println!("Next: cd {name} && zebra status");
    Ok(())
}
