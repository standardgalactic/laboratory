use std::collections::{HashSet, VecDeque};

use crate::model::TaskSet;

/// Breadth-first walk downstream from `start` (what consumes this,
/// directly or indirectly) — powers `zebra trace`.
pub fn trace_downstream(tasks: &TaskSet, start: &str) -> Vec<(usize, String)> {
    bfs(start, |n| tasks.direct_dependents(n))
}

/// Breadth-first walk upstream from `start` (what this depends on,
/// directly or indirectly) — powers `zebra why`.
pub fn trace_upstream(tasks: &TaskSet, start: &str) -> Vec<(usize, String)> {
    bfs(start, |n| {
        tasks
            .by_name
            .get(n)
            .map(|t| tasks.direct_deps(t))
            .unwrap_or_default()
    })
}

fn bfs(start: &str, neighbors: impl Fn(&str) -> Vec<String>) -> Vec<(usize, String)> {
    let mut seen: HashSet<String> = HashSet::new();
    let mut queue: VecDeque<(usize, String)> = VecDeque::new();
    let mut out = Vec::new();

    queue.push_back((0, start.to_string()));
    seen.insert(start.to_string());

    while let Some((depth, node)) = queue.pop_front() {
        out.push((depth, node.clone()));
        for next in neighbors(&node) {
            if seen.insert(next.clone()) {
                queue.push_back((depth + 1, next));
            }
        }
    }
    out
}
