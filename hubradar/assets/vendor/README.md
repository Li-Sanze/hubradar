# Mermaid offline runtime

Mermaid **11.17.2**, copied unchanged from the single-file browser build shipped
with Markdown Preview Enhanced **0.8.36** (`crossnote/dependencies/mermaid/mermaid.min.js`).

- Upstream: https://github.com/mermaid-js/mermaid/tree/mermaid@11.17.2
- License: `MERMAID-LICENSE.txt`; dependency notices remain in the JavaScript.
- SHA-256: `581ed7d74bd9048d0e3a91363927d72ef22942d7722546b27f7cc29e35390eb8`
- Original size: 3,572,661 bytes.

The runtime is included in both the wheel and generated HTML. No editor
extension, private Skill, CDN, or network service is required by the reader.
The full MIT notice is included in exported HTML alongside the original bundle.

When upgrading, replace the bundle and metadata together, preserve notices,
then run the browser regression fixtures offline and rebuild the wheel.
Do not replace this file with an ESM entry that fetches sibling chunks.
