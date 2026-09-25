//! Mechanical projection of SENS-owned profile-scoped mechanism admission.
//!
//! Authority lives in lib/function-table-mechanisms.lisp.
//! This module may only answer whether one already-selected Core admits a
//! mechanical route for one exact SENS function.

use crate::{CoreProfile, Sens8};

mod generated {
    include!("profile_mechanisms_generated.rs");
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ProfileMechanismRoute {
    RegisteredHostMechanism,
}

pub(crate) fn route_for(
    profile: Option<CoreProfile>,
    sens: Sens8,
) -> Option<ProfileMechanismRoute> {
    let profile = profile?;
    generated::PROFILE_MECHANISM_ROWS
        .iter()
        .find(|row| row.profile == profile && row.sens == sens)
        .map(|row| match row.route {
            generated::GeneratedProfileMechanismRoute::RegisteredHostMechanism => {
                ProfileMechanismRoute::RegisteredHostMechanism
            }
        })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn projection_contains_only_the_current_core3_raw_host_admission() {
        assert_eq!(
            route_for(Some(CoreProfile::Core3), crate::sens!(10101000)),
            Some(ProfileMechanismRoute::RegisteredHostMechanism)
        );
        assert_eq!(
            route_for(Some(CoreProfile::Core4), crate::sens!(10101000)),
            None
        );
        assert_eq!(
            route_for(Some(CoreProfile::Core3), crate::sens!(11111111)),
            None
        );
        assert_eq!(route_for(None, crate::sens!(10101000)), None);
    }
}
