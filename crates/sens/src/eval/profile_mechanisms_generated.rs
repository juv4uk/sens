// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/function-table-mechanisms.lisp (profile-routes)
// Generator: scripts/generate-rust-profile-mechanism-routes.lisp

use crate::{CoreDomainIdentity, CoreProfile};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[allow(dead_code)]
pub(crate) enum ProfileMechanismRouteKind {
    RegisteredHostMechanism,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ProfileMechanismRoute {
    profile: CoreProfile,
    sens: CoreDomainIdentity,
    kind: ProfileMechanismRouteKind,
}

const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRoute] = &[];

pub(crate) fn profile_mechanism_route(
    profile: CoreProfile,
    sens: CoreDomainIdentity,
) -> Option<ProfileMechanismRouteKind> {
    PROFILE_MECHANISM_ROUTES
        .iter()
        .find(|row| row.profile == profile && row.sens == sens)
        .map(|row| row.kind)
}
