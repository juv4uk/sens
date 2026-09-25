// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/function-table-mechanisms.lisp profile-rows
// Generator: scripts/generate-rust-profile-mechanisms.lisp

use crate::{CoreProfile, Sens8};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ProfileMechanismRoute {
    RegisteredHostMechanism,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct ProfileMechanismRow {
    pub(crate) profile: CoreProfile,
    pub(crate) function: Sens8,
    pub(crate) route: ProfileMechanismRoute,
}

pub(crate) const PROFILE_MECHANISM_ROUTES: &[ProfileMechanismRow] = &[
    ProfileMechanismRow { profile: CoreProfile::Core3, function: crate::sens!(10101000), route: ProfileMechanismRoute::RegisteredHostMechanism },
];

pub(crate) fn profile_mechanism_route(
    profile: Option<CoreProfile>,
    function: Sens8,
) -> Option<ProfileMechanismRoute> {
    let profile = profile?;
    PROFILE_MECHANISM_ROUTES
        .iter()
        .find(|row| row.profile == profile && row.function == function)
        .map(|row| row.route)
}
