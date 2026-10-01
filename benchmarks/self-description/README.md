# #2027 selector self-description benchmark

This research-only harness compares four ways to explain the same proven selector
identity without human names:

- flat explicit metadata row;
- compact root+suffix proof certificate;
- typed parent/generator graph traversal;
- hybrid: graph verifies distinct words during preparation, certificate serves hot explanations.

All routes must reconstruct the same name-erased explanation tuple:
`(root, suffix, depth)`.

The benchmark keeps storage/fact counts and CPU instruction cost separate.
