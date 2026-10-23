#!/usr/bin/env python3
"""Conservative, checked prose edits for compression-without-verification.tex.
Preview by default; use --apply to write a timestamped backup and edit the file.
"""
from pathlib import Path
import argparse
import difflib
import re
from datetime import datetime

p = argparse.ArgumentParser()
p.add_argument('--file', type=Path, default=Path('compression-without-verification.tex'))
p.add_argument('--apply', action='store_true')
a = p.parse_args()
original = a.file.read_text(encoding='utf-8')
changes = [
('Abstract: avoid treating interpretation as established mechanism',
 'This essay accepts the paper\'s empirical core and its local mechanism, and argues that the mechanism is best understood primarily as a change in continuation geometry and not as the acquisition of new problem-solving knowledge,',
 'This essay accepts the paper\'s empirical core and takes its proposed local mechanism seriously, while arguing that the gains are best understood primarily as a change in continuation geometry rather than as demonstrated acquisition of new problem-solving knowledge,'),
('Introduction: distinguish result from proposed mechanism',
 'The paper under discussion supplies a rare, well-controlled, real-model case of exactly this kind of reorganization,',
 'The paper under discussion supplies a rare, substantial real-model improvement consistent with this kind of reorganization,'),
('Empirical assessment: avoid claiming impossibility of selection artifacts',
 'This does not undermine the qualitative finding that SSD helps, which is too large and too consistent across models to be an artifact of this kind, but it does mean the precise magnitudes reported for any one configuration should be read as optimistic rather than as a stable estimate of what the method delivers under a fixed, pre-registered configuration.',
 'This does not by itself overturn the qualitative finding that SSD helps, which recurs across the tested models, but it does mean that the precise magnitudes reported for selected configurations may be optimistic relative to estimates obtained under a fixed, preregistered protocol.'),
('Continuation geometry: avoid claiming lossless equivalence',
 'The lock and fork vocabulary can be restated without loss in terms already developed elsewhere in this program, and doing so exposes what kind of object SSD is actually acting on.',
 'The lock and fork vocabulary can be redescribed in terms developed elsewhere in this program, although the translation remains interpretive rather than an independently tested mechanism.'),
('Continuation geometry: distinguish hypothesis from direct demonstration',
 'SSD does not resolve this mismatch by adding a second control parameter. It resolves it by changing the substrate the single parameter acts on,',
 'On the proposed account, SSD does not resolve this mismatch by adding a second control parameter. Instead, it changes the substrate the single parameter acts on,'),
('Framework: avoid conflating theoretical prediction with empirical isolation',
 'The paper is an unusually clean instance of the general claim that capability is not equivalent to representational presence.',
 'The paper offers a useful case for examining the claim that capability is not equivalent to representational presence.'),
('Lifecycle: remove implication that every constant verifier is always invalid',
 'a verifier\nthat returns a constant certifies nothing, and a pipeline can run to\ncompletion on it.',
 'a verifier that remains constant when the reference-relevant input varies provides no evidence that it tracks that variation, and a pipeline can run to completion despite this failure.'),
('Lifecycle: distinguish benchmark selection from direct verifier gaming',
 'checkpoint selection of that kind is\na mild form of pre-commit access to the evaluator.',
 'checkpoint selection of that kind introduces an opportunity for selection on the evaluator, without itself demonstrating deliberate gaming.'),
('Lifecycle: avoid claiming complete verification from four conditions',
 'The refinement these papers support can be stated as four conditions that must hold together for a consequential transformation to count as verified.',
 'The refinement these papers support can be stated as four necessary safeguards for a consequential transformation to warrant a strong verification claim; satisfying them would not, by itself, establish every form of correctness or safety.'),
('Conclusion: avoid calling unverified admission verified',
 'Verified admission does not complete the compression claim.',
 'Even successful post-training evaluation does not complete the verification of a consequential compression or deployment.'),
]
updated = original
for label, old, new in changes:
    count = updated.count(old)
    if count != 1:
        raise SystemExit(f'STOP: {label}: expected one exact match, found {count}. No file changed.')
    updated = updated.replace(old, new, 1)
    print('OK:', label)
print('\n' + ''.join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), fromfile='original', tofile='polished')))
if a.apply:
    backup = a.file.with_name(a.file.name + '.bak-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    if backup.exists():
        raise SystemExit(f'Backup already exists: {backup}')
    backup.write_text(original, encoding='utf-8')
    a.file.write_text(updated, encoding='utf-8')
    print(f'Applied {len(changes)} edits. Backup: {backup}')
else:
    print(f'Preview only: {len(changes)} edits. Re-run with --apply to write.')

