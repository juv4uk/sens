// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/function-table-mechanisms.lisp (profile-routes)
// Generator: scripts/generate-rust-profile-mechanism-routes.lisp

use crate::{CoreProfile, Sens8};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ProfileMechanismRouteKind {
    RegisteredHostMechanism,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ProfileMechanismRoute {
    profile: CoreProfile,
    sens: Sens8,
    kind: ProfileMechanismRouteKind,
}

const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRoute] = &[
    ProfileMechanismRoute { profile: CoreProfile::Core3, sens: crate::sens!(10101000), kind: ProfileMechanismRouteKind::RegisteredHostMechanism },
];

pub(crate) fn profile_mechanism_route(
    profile: CoreProfile,
    sens: Sens8,
) -> Option<ProfileMechanismRouteKind> {
    PROFILE_MECHANISM_ROUTES
        .iter()
        .find(|row| row.profile == profile && row.sens == sens)
        .map(|row| row.kind)
}
