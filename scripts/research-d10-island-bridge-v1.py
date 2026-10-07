#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Tuple

@dataclass(frozen=True)
class NativeObservation:
    producer: str
    results: Tuple[Any, ...]
    provenance: Tuple[Tuple[str, str], ...]

def result_count(obs: NativeObservation) -> int:
    return len(obs.results)

def zero_results(obs: NativeObservation) -> bool:
    return result_count(obs) == 0

def one_result(obs: NativeObservation) -> bool:
    return result_count(obs) == 1

def many_results(obs: NativeObservation) -> bool:
    return result_count(obs) > 1

@dataclass(frozen=True)
class MissingCapability:
    kind: str
    detail: str

def missing_kernel(name: str) -> MissingCapability:
    return MissingCapability("kernel", name)

def missing_bridge(name: str) -> MissingCapability:
    return MissingCapability("bridge", name)

def explicit_projection(obs: NativeObservation, fn):
    return fn(obs)

def bridge(source: NativeObservation, projector):
    # Explicit partial conversion; source stays unchanged.
    projected = projector(source)
    return source, projected

def main() -> int:
    zero = NativeObservation("clips", (), (("repo","clips-kernel"),))
    one = NativeObservation("prolog", ("yes",), (("repo","prolog-kernel"),))
    many = NativeObservation("datalog", ("a","b","c"), (("repo","datalog-kernel"),))

    assert result_count(zero) == 0 and zero_results(zero)
    assert result_count(one) == 1 and one_result(one)
    assert result_count(many) == 3 and many_results(many)

    # ZERO/ONE/MANY add no independent information beyond RESULT-COUNT.
    assert (zero_results(zero), one_result(zero), many_results(zero)) == (True, False, False)
    assert (zero_results(one), one_result(one), many_results(one)) == (False, True, False)
    assert (zero_results(many), one_result(many), many_results(many)) == (False, False, True)

    mk = missing_kernel("cuda")
    mb = missing_bridge("clips->lisp")
    assert mk.kind == "kernel" and mb.kind == "bridge"
    assert isinstance(mk, MissingCapability) and isinstance(mb, MissingCapability)

    # Explicit projection is ordinary application of a caller-supplied function.
    projected = explicit_projection(one, lambda obs: list(obs.results))
    assert projected == ["yes"]

    # Bridge preserves source observation and keeps conversion explicit.
    source, target = bridge(many, lambda obs: tuple(reversed(obs.results)))
    assert source is many
    assert target == ("c","b","a")
    assert source.results == ("a","b","c")

    # Provenance is data carried by the observation, not a new island-only truth.
    assert dict(one.provenance)["repo"] == "prolog-kernel"

    print("D10-ISLAND-BRIDGE-WITNESS=PASS")
    print("result-count factors zero/one/many; missing-capability factors kernel/bridge; projection explicit")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
