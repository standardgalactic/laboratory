# Dependency Ledger: The Flyxion Papers (v3)

This ledger serves as the canonical map of the mesh for *The Flyxion Papers: Verification, Design Axioms, and Holonomy*. It establishes a directed acyclic graph over the monograph's 22 chapters, structured so that no chapter references conceptual vocabulary, mathematical formalisms, or systems-level assertions not already established in its parent nodes.

**v3 change:** `clarification-without-retrieval.pdf` reassigned from Ch. 4 to Ch. 12/13's source list, since its actual subject (name resolution vs. specification resolution, forensic implementation, provenance-disciplined reconstruction) fits the Verify Seams / Verification Inheritance chapters more directly than the Paracosm Trap chapter. Ch. 4 is now anchored solely on `glass-meridian.pdf`, which is a direct, undiluted match for the paracosm-trap argument (Wilkins/Borges, the isolated internally-rigorous private system, the Lacanian/DHT dual reading and Nuspeak convergence demonstration).

---

## I. The Global Dependency Matrix

| Chapter | Title | Primary Source File | Drafting Status | Direct Dependencies (Cites) | Dependent Successors (Cited By) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ch. 1** | *The Latency of Evidence* | `latency-of-evidence.pdf` | Fully Drafted | *None* | Ch. 5, Ch. 10, Ch. 22 |
| **Ch. 2** | *Accommodation Before Prediction* | `accommodation-before-prediction.pdf` & `narrative-before-mechanism.pdf` | Fully Drafted | *None* | Ch. 5, Ch. 10, Ch. 22 |
| **Ch. 3** | *The Theatre of Agreement* | `consensus-without-independence.pdf` | Fully Drafted | *None* | Ch. 5, Ch. 10 |
| **Ch. 4** | *The Paracosm Trap* | `glass-meridian.pdf` | Fully Drafted | *None* | Ch. 5 |
| **Ch. 5** | *The Ontological Reversal* | *Connector (Ontology Shift)* | **Fresh** | Ch. 1, Ch. 2, Ch. 3, Ch. 4 | Ch. 6, Ch. 7 |
| **Ch. 6** | *Distinction Holonomy Theory* | `distinction-holonomy.pdf` (Part I) | Fully Drafted | Ch. 5 | Ch. 7, Ch. 8, Ch. 9, Ch. 10, Ch. 22 |
| **Ch. 7** | *Spherepop: An Event Calculus* | `distinction-holonomy.pdf` (Part II) | Fully Drafted | Ch. 6 | Ch. 8, Ch. 10, Ch. 20 |
| **Ch. 8** | *TARTAN Tiling & RSVP* | `distinction-holonomy.pdf` & `everything_is_contextual_revised.pdf` | Hybrid | Ch. 6, Ch. 7 | Ch. 10, Ch. 22 |
| **Ch. 9** | *The Discrete Toy Model* | `distinction-holonomy.pdf` (App. D) | Fully Drafted | Ch. 6 | *None* |
| **Ch. 10** | *The CLIO Architecture* | `from-verification-to-commitment.pdf` | Fully Drafted | Ch. 1, Ch. 2, Ch. 3, Ch. 6, Ch. 7, Ch. 8 | Ch. 11, Ch. 12, Ch. 13, Ch. 20, Ch. 22 |
| **Ch. 11** | *The Constitutional Space of Refusal* | `Rebel Without a Cost.pdf` (§10-10.2) | Fully Drafted | Ch. 10 | Ch. 20 |
| **Ch. 12** | *Verify Seams & Workarounds* | `two-verify-seams.pdf`, `epistemology-of-repair.pdf` & `clarification-without-retrieval.pdf` | Hybrid | Ch. 10 | Ch. 13 |
| **Ch. 13** | *Verification Inheritance* | `manifest-protocol-verification-inheritance.pdf`, `verification-inheritance-transformation.pdf` & `clarification-without-retrieval.pdf` | Hybrid | Ch. 10, Ch. 12 | Ch. 14 |
| **Ch. 14** | *Model Capsules & Ternary Learning* | `deployment_native_ternary_learning.pdf` | Fully Drafted | Ch. 13 | Ch. 15 |
| **Ch. 15** | *The Compression Fallacy* | `compression-fallacy.pdf` / `The_Compression_Fallacy.pdf` | Fully Drafted | Ch. 14 | Ch. 16, Ch. 17, Ch. 18, Ch. 19, Ch. 20, Ch. 22 |
| **Ch. 16** | *Compression After Expansion* | `compression_after_expansion.pdf` & `Borrowed_Intuition.pdf` | Hybrid | Ch. 15 | Ch. 20 |
| **Ch. 17** | *Sparse Holographic Steganography* | `sparse-recursive-holographic-steganography.pdf` | Fully Drafted | Ch. 15 | *None* |
| **Ch. 18** | *Clifford FHE as Inverse Case* | `rsta.2025.0107.pdf` | Fully Drafted | Ch. 15 | *None* |
| **Ch. 19** | *Ledgers Without Value* | `ledger-without-value.pdf` | Fully Drafted | Ch. 15 | Ch. 20, Ch. 22 |
| **Ch. 20** | *Rebel Without a Cost* | `Rebel Without a Cost.pdf` (§1-9) | Hybrid | Ch. 7, Ch. 10, Ch. 11, Ch. 15, Ch. 16, Ch. 19 | Ch. 21, Ch. 22 |
| **Ch. 21** | *Unfinishable Games & Temporal Extraction* | `unfinishable-games.pdf` | Fully Drafted | Ch. 20 | Ch. 22 |
| **Ch. 22** | *Sheaves of Necessity and Affordability* | `debt-before-deflation.pdf` | Hybrid | Ch. 1, Ch. 2, Ch. 6, Ch. 8, Ch. 10, Ch. 15, Ch. 19, Ch. 20, Ch. 21 | *None* (Synthesis Node) |

---

## II. Detailed Node Schemas & Rationale

### Part I: Epistemic Foundations (Chapters 1–4)
*   **Ch. 1: The Latency of Evidence** (Source: `latency-of-evidence.pdf`)
    *   *Role:* Foundational anchor for the distinction between raw physical trace ($X_t$), semantic and evidential legibility ($L_t$), institutional admissibility ($A_t$), and downstream operational consequence ($C_t$).
    *   *Dependencies:* None.
*   **Ch. 2: Accommodation Before Prediction** (Source: `accommodation-before-prediction.pdf` & `narrative-before-mechanism.pdf`)
    *   *Role:* Critiques explanatory over-coherence ($\Lambda(O) \approx 1$) and accommodative over-flexibility. Co-sourced with `narrative-before-mechanism.pdf` to ground the "Doomsday Ratchet" metaphor and its narrative prehistory in a mathematically precise flat-likelihood framework.
    *   *Dependencies:* None.
*   **Ch. 3: The Theatre of Agreement** (Source: `consensus-without-independence.pdf`)
    *   *Role:* Identifies the "phenomenology of social confirmation" and the danger of recursive consensus inflation inside persona ensembles.
    *   *Dependencies:* None.
*   **Ch. 4: The Paracosm Trap** (Source: `glass-meridian.pdf`)
    *   *Role:* Demonstrates, via a dual Lacanian/distinction-holonomy reading of an invented lyric text and a controlled Nuspeak convergence test, how an isolated, internally rigorous private system (a paracosm) mistakes internal coherence for collective, adversarial, revisable warrant. Traces the Wilkins/Borges lineage of the pattern.
    *   *Dependencies:* None.

### Part II: The Geometry of Persistence (Chapters 5–9)
*   **Ch. 5: Connective Bridge: The Ontological Reversal** (Fresh Chapter)
    *   *Role:* Bridges Part I and Part II by arguing that the failures of Chapters 1–4 share a common pathology: the reliance on static state-equality as the basis of identity. Introduces identity as the transport of admissible distinctions through transformation.
    *   *Dependencies:* Ch. 1, Ch. 2, Ch. 3, Ch. 4.
*   **Ch. 6: Distinction Holonomy Theory (DHT)** (Source: `distinction-holonomy.pdf` Part I)
    *   *Role:* Establishes the core mathematical grammar: parallel transport, connection ($A_\mu$), curvature ($F$), and memory as path-dependent transport.
    *   *Dependencies:* Ch. 5.
*   **Ch. 7: Spherepop: An Event-Sourced Calculus of Time** (Source: `distinction-holonomy.pdf` Part II)
    *   *Role:* Specializes DHT to discrete evaluation. Generates a noninvertible, categorical connection where noncommutativity of Spherepop's four primitives (Pop, Refuse, Bind, Collapse) creates literal curvature.
    *   *Dependencies:* Ch. 6.
*   **Ch. 8: TARTAN: Recursive Multiscale Tiling** (Source: `distinction-holonomy.pdf` Part II & `everything_is_contextual_revised.pdf`)
    *   *Role:* Couples Spherepop's discrete events to continuous field substrates (RSVP) via multiscale sheaves, defining scale-coherent persistence.
    *   *Dependencies:* Ch. 6, Ch. 7.
*   **Ch. 9: The Discrete Toy Model** (Source: `distinction-holonomy.pdf` App. D)
    *   *Role:* Standalone mathematical demonstration of noncommutativity over $\mathbf{R}^2$ using matrix generators.
    *   *Dependencies:* Ch. 6.

### Part III: Systems and Admissibility (Chapters 10–14)
*   **Ch. 10: The CLIO Architecture** (Source: `from-verification-to-commitment.pdf`)
    *   *Role:* Implements Part I's epistemic bookkeeping at the software layer. Separation of documentary history ($H_t$) from operative state ($\sigma_t$).
    *   *Dependencies:* Ch. 1, Ch. 2, Ch. 3 (epistemic grounds), Ch. 6, Ch. 7, Ch. 8 (geometric grounds).
*   **Ch. 11: The Constitutional Space of Refusal** (Source: `Rebel Without a Cost.pdf` §10)
    *   *Role:* Formalizes the mathematical validity of non-action and the option-cost of commitment ($\Delta\Omega(r)$).
    *   *Dependencies:* Ch. 10.
*   **Ch. 12: Verify Seams & Workarounds** (Source: `two-verify-seams.pdf`, `epistemology-of-repair.pdf` & `clarification-without-retrieval.pdf`)
    *   *Role:* Examines "verify seams" $(\sigma, \rho)$ where consequence propagates while reasoning is withheld. Defines workarounds as causal theorems. `clarification-without-retrieval.pdf` contributes the specification-gap taxonomy (complete/ambiguous/incoherent/underdetermined) and the name-resolution-vs-specification-resolution distinction as a concrete case of a verify seam operating at the level of an implementation request rather than a running system.
    *   *Dependencies:* Ch. 10.
*   **Ch. 13: Verification Inheritance** (Source: `manifest-protocol-verification-inheritance.pdf`, `verification-inheritance-transformation.pdf` & `clarification-without-retrieval.pdf`)
    *   *Role:* Establishes the 3-valued routing of Claimshift under the undecidability of semantic correspondence. `clarification-without-retrieval.pdf` supplies the MEM|8 case study — nominal, genealogical, structural, and behavioral continuity as four non-implying relations across a family of same-named artifacts — as a worked instance of verification failing to transfer across a transformation.
    *   *Dependencies:* Ch. 10, Ch. 12.
*   **Ch. 14: Model Capsules & Ternary Learning** (Source: `deployment_native_ternary_learning.pdf`)
    *   *Role:* Seals the deployment-gap by embedding the forward operator as a training constraint in signed capsules.
    *   *Dependencies:* Ch. 13.

### Part IV: Representations and Compression (Chapters 15–18)
*   **Ch. 15: The Compression Fallacy** (Source: `compression-fallacy.pdf`)
    *   *Role:* Proves that description length ($L_T$), distinguishing capacity ($D_T$), and operational repertoire ($O_T$) are independent coordinates. Shows how brevity in representation simply displaces complexity into the background decoder ($M_T$).
    *   *Dependencies:* Ch. 14.
*   **Ch. 16: Compression After Expansion** (Source: `compression_after_expansion.pdf` & `Borrowed_Intuition.pdf`)
    *   *Role:* Analyzes expert automaticity as the relegation of previously deliberate, expanded procedures.
    *   *Dependencies:* Ch. 15.
*   **Ch. 17: Sparse Holographic Steganography** (Source: `sparse-recursive-holographic-steganography.pdf`)
    *   *Role:* Replaces localized symbol writing with the holographic projection of secret fields over a sparse active set.
    *   *Dependencies:* Ch. 15.
*   **Ch. 18: Clifford FHE as Inverse Case** (Source: `rsta.2025.0107.pdf`)
    *   *Role:* Explores homomorphic evaluation where operational structure ($O_T$) is preserved at the cost of massive physical footprint expansion ($L_T$).
    *   *Dependencies:* Ch. 15.

### Part V: The Political Economy of Extraction (Chapters 19–22)
*   **Ch. 19: Ledgers Without Value** (Source: `ledger-without-value.pdf`)
    *   *Role:* Critiques cryptocurrency by showing that cryptographic consistency (log-admissibility) does not imply thermodynamic productivity.
    *   *Dependencies:* Ch. 15.
*   **Ch. 20: Rebel Without a Cost** (Source: `Rebel Without a Cost.pdf` §1-9)
    *   *Role:* Unbundles the contribution pipeline. Formulates the "Ayian" as a non-transferable, witnessed unit of continuation over a partially ordered poset.
    *   *Dependencies:* Ch. 7, Ch. 10, Ch. 11, Ch. 15, Ch. 16, Ch. 19.
*   **Ch. 21: Unfinishable Games & Temporal Extraction** (Source: `unfinishable-games.pdf`)
    *   *Role:* Examines how persistent social systems capture uncompensated player coordination labor by coupling state-integrity to continuous personal exposure.
    *   *Dependencies:* Ch. 20.
*   **Ch. 22: Sheaves of Necessity and Affordability** (Source: `debt-before-deflation.pdf`)
    *   *Role:* The monograph's synthesis node. Exposes global composition failures of locally consistent affordability judgments using sheaf theory.
    *   *Dependencies:* Ch. 1, Ch. 2, Ch. 6, Ch. 8, Ch. 10, Ch. 15, Ch. 19, Ch. 20, Ch. 21.

---

## III. The 5-Phase Drafting Pipeline (Topological Sort)

Drafting proceeds along five sequential horizons. No phase begins until its preceding phase is frozen:

```
[Phase 1: Epistemic Anchors] (Ch. 1, 2, 3, 4)
             |
             v
[Phase 2: Geometric & Connective Core] (Ch. 5, 6, 9)
             |
             v
[Phase 3: The Event Calculus & Tiling] (Ch. 7, 8)
             |
             v
[Phase 4: Systems, Verification & Representation] (Ch. 10, 11, 12, 13, 14, 15, 17, 18)
             |
             v
[Phase 5: The Political Economy Synthesis] (Ch. 16, 19, 20, 21, 22)
```

1.  **Phase 1: Epistemic Anchors** (Chapters 1, 2, 3, 4) — Fully grounded; all four chapters have confirmed, on-theme sources.
2.  **Phase 2: Geometric & Connective Core** (Chapters 5, 6, 9) — Establishes the continuous DHT connection.
3.  **Phase 3: The Event Calculus & Tiling** (Chapters 7, 8) — Constructs discrete Spherepop evaluation over TARTAN structures.
4.  **Phase 4: Systems, Verification, and Representation** (Chapters 10, 11, 12, 13, 14, 15, 17, 18) — Implements CLIO, Verify Seams (now with the MEM|8/specification-drift case study), Claimshift, Model Capsules, and the core proof of the Compression Fallacy.
5.  **Phase 5: The Political Economy Synthesis** (Chapters 16, 19, 20, 21, 22) — Unifies the unbundled contribution pipeline, temporal extraction, and the sheaf-theoretic postscript of affordability.
