// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/function-table-mechanisms.lisp profile-rows
// Generator: scripts/generate-rust-profile-mechanisms.lisp

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum GeneratedProfileMechanismRoute {
    RegisteredHostMechanism,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) struct GeneratedProfileMechanismRow {
    pub(super) profile: crate::CoreProfile,
    pub(super) sens: crate::Sens8,
    pub(super) route: GeneratedProfileMechanismRoute,
}

pub(super) const PROFILE_MECHANISM_ROWS: &[GeneratedProfileMechanismRow] = &[
    GeneratedProfileMechanismRow { profile: crate::CoreProfile::Core3, sens: crate::sens!(10101000), route: GeneratedProfileMechanismRoute::RegisteredHostMechanism },
];
