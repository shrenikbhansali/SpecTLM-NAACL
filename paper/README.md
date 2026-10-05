# Anonymous ACL/ARR drafting skeleton

Two alternatives share the opening, background, atlas setup, limitations, ethics,
appendices, numeric macros, and figure directory. Neither alternative selects the
paper framing or contains experimental claims. All prose remains explicitly marked
for owner drafting.

Run the complete W1 acceptance check from the repository root:

```sh
python -m pytest paper/tests/test_compile.py -q -s
```

This compiles both mains with `latexmk -pdf`, official ACL review mode, and the
vendored style directory on `TEXINPUTS`. It prints page counts and rejects LaTeX
errors and undefined references. Generated files go into temporary directories.
The local TeX installation needs the official style's dependencies, including
`caption`, `upquote`, `inconsolata`, `microtype`, and `natbib`.

The unmodified official style files are pinned by revision and SHA-256 in
`style/source.json`. Populate `shared/references.bib` and enable the bibliography
lines when citations are added. B13 owns generated numeric macros in `numbers.tex`;
B12 owns figures and provenance sidecars in `figures/`.
