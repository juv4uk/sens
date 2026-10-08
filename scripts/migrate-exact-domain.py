}

ROW_RE = re.compile(r'^\s*\(([01]{8})\s+(.*)\)\s*$')
FIELD_RE = re.compile(
    r'\((en|uk|ukr|sa|sym)\s+("(?:\\\\.|[^"\\\\])*"|\(\)|[^()\s]+)\)'
)


@dataclass(frozen=True)
class Identity:
    domain: str
    bits: str
    label: str


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    source: str
    identity: Identity


def decode_registry_value(raw: str) -> str | None: