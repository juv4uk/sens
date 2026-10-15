from pathlib import Path
_a = Path(__file__).with_name("_migration_zig_gate_body_a.py").read_text(encoding="utf-8")
_b = Path(__file__).with_name("_migration_zig_gate_body_b.py").read_text(encoding="utf-8")
exec(compile(_a + _b, str(Path(__file__).resolve()), "exec"), globals())
