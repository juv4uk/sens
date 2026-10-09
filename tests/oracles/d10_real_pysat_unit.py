#!/usr/bin/env python3
"""Independent compiled SAT-engine BCP donor: PySAT Glucose3.propagate."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_d10_dll1962_unit_closure import real_donor_corpus, unit_closure
from pysat import __version__ as pysat_version
from pysat.solvers import Glucose3


def main():
    compatible = conflicts = 0
    for case_number, (cnf, assumptions) in enumerate(real_donor_corpus()):
        pure = unit_closure(cnf, assumptions)
        with Glucose3(bootstrap_with=cnf) as solver:
            status, observed = solver.propagate(assumptions=assumptions)
        if pure["status"] == "CONTRADICTION":
            if status:
                raise AssertionError(
                    f"real compiled SAT donor missed unit conflict case={case_number}, "
                    f"cnf={cnf}, assumptions={assumptions}, observed={observed}")
            conflicts += 1
        else:
            if not status:
                raise AssertionError(
                    f"real SAT donor produced false unit conflict at {case_number}")
            # PySAT returns *new* propagations due to assumptions, and MAY
            # omit CNF root-level units already cached during bootstrap.
            # Therefore equality of the API list to the mathematical full
            # closure would be false. Check every reported literal is in our
            # closure, then independently force the opposite of *every*
            # mathematical implication: real Glucose3 BCP must conflict.
            if not set(observed).issubset(set(pure["forced"])):
                raise AssertionError(
                    f"compiled SAT donor invented a literal case={case_number}: "
                    f"actual={sorted(observed)}, exact_closure={pure['forced']}")
            for forced in pure["forced"]:
                with Glucose3(bootstrap_with=cnf) as second_solver:
                    opposite_ok, _ = second_solver.propagate(
                        assumptions=sorted(assumptions + [-forced]))
                if opposite_ok:
                    raise AssertionError(
                        f"real compiled Glucose3 BCP did not imply {forced}; "
                        f"case={case_number} cnf={cnf} assumptions={assumptions}")
            compatible += 1
    assert compatible > 0 and conflicts > 0
    assert compatible + conflicts == 600
    print(f"D10-DLL1962 REAL-PYSAT {pysat_version} "
          f"Glucose3.propagate PASS 600/600 conflict={conflicts} quiescent={compatible}")
    print("D10-DLL1962 donor is an external Boolean BCP runtime, "
          "NOT SENS execution, owner ratification or D10 identity.")


if __name__ == "__main__":
    main()
