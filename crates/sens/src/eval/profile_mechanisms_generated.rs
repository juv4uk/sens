// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/function-table-mechanisms.lisp (lab-routes)
// Generator: scripts/generate-rust-profile-mechanism-routes.lisp

use crate::Sens8;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MechanismLabRouteKind {
    RegisteredHostMechanism,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct MechanismLabRoute {
    sens: Sens8,
    kind: MechanismLabRouteKind,
}

const MECHANISM_LAB_ROUTES: &[MechanismLabRoute] = &[
    MechanismLabRoute { sens: crate::sens!(10101000), kind: MechanismLabRouteKind::RegisteredHostMechanism },
];

pub(crate) fn mechanism_lab_route(sens: Sens8) -> Option<MechanismLabRouteKind> {
    MECHANISM_LAB_ROUTES
        .iter()
        .find(|row| row.sens == sens)
        .map(|row| row.kind)
}
