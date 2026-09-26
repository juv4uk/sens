//! Semantic Atom Registry — Sanskrit migration Phase 2/3/4
//! (docs/sanskrit-semantic-migration.md §3, §18, §4, §5).
//!
//! The single authoritative source of semantic atoms. Phase 2 delivered
//! the *registry mechanism* proven against the spec's own worked example
//! (`DHATU_DA`); Phase 3 (`SANSKRIT-P3-DHATU-CORE`) populated the full
//! 12-dhātu core with exact per-atom semantics per spec §18; Phase 4
//! (`SANSKRIT-P4-KARAKA-LAYER`, this addition) adds the six kāraka roles
//! and `karaka.rs`'s `SemanticCall` AST type. Keeping each phase in its
//! own commit is what spec §34 means by "не виконувати всі фази одним
//! commit".
//!
//! Every dhātu's `slp1`/`gaṇa`/lexicographic sense here is doubly
//! sourced, not invented: cross-checked against `sens-panini`'s
//! `panini/registry/dhatu/*.yaml` (itself verified against
//! `vidyut-prakriya/data/dhatupatha.tsv`, the Vidyut project's structured
//! Dhātupāṭha — see that repo's `panini/research/dhatupatha-verification.md`
//! and `docs/sanskrit-lexicon-verification.md` in *this* repo, which
//! independently verified the same 12 roots against Monier-Williams-
//! derived web sources before `sens-panini`'s registry existed). Where
//! sources agreed (all 12), that is the sense filed below; the *chosen
//! programming-language operational meaning* per root (spec §4: "Мова
//! програмування повинна вибрати чітку operational semantics") is this
//! task's own judgment call, informed by but not dictated by the
//! lexicographic sense — a Sanskrit root's classical senses are a
//! starting point, not a specification.
//!
//! The load-bearing design rule from spec §3: **the semantic `id` is the
//! identity, never the SLP1 spelling.** `DHATU_DA -> dA` is correct;
//! treating `"dA"` itself as the identity is not — that would tie AST/
//! bytecode/ABI stability to orthography, which spec §3 exists to avoid.
//! `atoms_test_no_identity_is_its_own_spelling` below enforces this
//! mechanically, not just as a doc comment.
//!
//! `status: Experimental` on every entry below is deliberate, not an
//! oversight: spec §18's full field shape (required/optional roles as
//! actual kāraka references, not prose) can't be finalized until
//! `SANSKRIT-P4-KARAKA-LAYER` exists to reference. Promoting to `Stable`
//! is P4's job, not this one's.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AtomCategory {
    Dhatu,
    Karaka,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AtomStatus {
    /// In the registry for pipeline validation but not yet vetted per
    /// spec §18's full exact-semantics writeup.
    Experimental,
    Stable,
    Deprecated,
}

#[derive(Debug, Clone, Copy)]
pub struct Atom {
    /// Stable identity — independent of spelling (spec §3). Never equals
    /// `slp1`.
    pub id: &'static str,
    /// Canonical ASCII storage spelling (spec §1: SLP1 is canonical).
    pub slp1: &'static str,
    /// Presentation-only romanization (spec §1: never an internal
    /// identifier). Must equal `transliteration::slp1_to_iast(slp1)` —
    /// enforced by test, so this can't silently drift from Phase 1's
    /// table.
    pub iast: &'static str,
    /// Presentation-only Devanāgarī spelling. Hand-verified against
    /// engineer-1's KARAKA-REFERENCE.md / PANINI-GRAMMAR-REFERENCE.md
    /// (themselves cross-checked against the Aṣṭādhyāyī), not invented —
    /// full SLP1<->Devanāgarī conversion is SANSKRIT-P2-DEVANAGARI-MAPPING,
    /// a separate task; these are literal, individually-sourced spellings.
    pub devanagari: &'static str,
    pub category: AtomCategory,
    /// Human-readable one-word gloss — a hint, never the formal semantics
    /// (spec §23: "Не використовувати англійський gloss як definition").
    pub gloss: &'static str,
    /// The formal operational semantics (spec §18). `SANSKRIT-P3` (dhātu)
    /// and `SANSKRIT-P4` (kāraka) own writing these out fully per-atom;
    /// Phase 2 entries carry a placeholder pending that pass, tracked via
    /// `status: Experimental`.
    pub semantics: &'static str,
    /// Legacy English names this atom subsumes (spec §13, feeds
    /// `SANSKRIT-P6-COMPAT-ALIASES`).
    pub aliases: &'static [&'static str],
    pub status: AtomStatus,
}

/// The 12-dhātu experimental core (spec §4), each gaṇa/sense doubly
/// sourced (see module docs). `semantics` follows spec §18's shape as
/// prose for now (required roles / optional roles / effects / purity) —
/// real `Karaka`-typed fields are P4's job once that type exists.
pub const REGISTRY: &[Atom] = &[
    Atom {
        id: "DHATU_KF",
        slp1: "kf",
        iast: "kṛ",
        devanagari: "कृ",
        category: AtomCategory::Dhatu,
        gloss: "make",
        semantics: "construct or perform: bring a new entity or action into being. required role: karman (what is made/done). optional roles: kartf (agent), karaRa (means/instrument). effects: typically constructive (allocation/construction of a value); purity: pure when karman denotes a value being constructed, impure when karman denotes an external action being performed — gaRa 8 (tanAdi) per panini/registry/dhatu/kf.yaml, cross-verified docs/sanskrit-lexicon-verification.md",
        aliases: &["make", "create", "construct"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_GAM",
        slp1: "gam",
        iast: "gam",
        devanagari: "गम्",
        category: AtomCategory::Dhatu,
        gloss: "go",
        semantics: "transition: move an entity from one state, location, or position in a sequence to another. required role: kartf (what transitions — gam is classically intransitive, the mover is the agent, not a separate object). optional roles: apAdAna (starting point), aDikaraRa (destination/target state). effects: state/position transition, no value construction; purity: pure for a logical/data-structure transition (e.g. iterator advance), impure for a transition with external effect (e.g. process/control transfer). gaRa 1 (BvAdi)",
        aliases: &["go", "next", "advance"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_DA",
        slp1: "dA",
        iast: "dā",
        devanagari: "दा",
        category: AtomCategory::Dhatu,
        gloss: "give",
        semantics: "transfer an entity from an agent (kartṛ) toward a recipient (sampradāna); required role karman, optional kartṛ/sampradāna — see spec §18 for the full field shape once SANSKRIT-P3 vets this beyond the worked example",
        aliases: &["give", "transfer", "send"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_GRAH",
        slp1: "grah",
        iast: "grah",
        devanagari: "ग्रह्",
        category: AtomCategory::Dhatu,
        gloss: "take",
        semantics: "acquire: bind a reference to, or take possession of, an entity. required role: karman (what is acquired). optional roles: kartf (agent), apAdAna (source it is taken from — the counterpart of dA's sampradAna). effects: acquisition of a reference/resource, may allocate a binding; purity: context dependent (pure if binding an already-existing value, impure if acquiring an external resource, e.g. a lock or handle). gaRa 9 (kryAdi)",
        aliases: &["take", "acquire", "grab"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_JNA",
        slp1: "jYA",
        iast: "jñā",
        devanagari: "ज्ञा",
        category: AtomCategory::Dhatu,
        gloss: "know",
        semantics: "cognize: query or introspect knowledge about a value's nature, without altering it. required role: karman (what is known/queried). optional roles: kartf (the one who knows). effects: none — read-only cognition; purity: pure, always (this is the classification-predicate family, e.g. a type test). deliberately distinct from eval per SANSKRIT-P1-DESIGN-DECISIONS, which explicitly ruled jYA must NOT be reused for eval's execute-an-expression sense (a separate root, chosen later, not yet assigned). gaRa 9 (kryAdi) — engineer-1's original reference and panini/registry/dhatu/jYA.yaml both note jYA appears under multiple gaRa/homonyms in the primary Dhatupatha; the gaRa-9 \"know\" sense is the one filed here, matching the docs/sanskrit-lexicon-verification.md finding",
        aliases: &["know?", "type-of"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_DRS",
        slp1: "dfS",
        iast: "dṛś",
        devanagari: "दृश्",
        category: AtomCategory::Dhatu,
        gloss: "see",
        semantics: "observe: inspect a value already in hand, without retrieving it from an external source (contrast paW, which implies retrieval from a source/medium). required role: karman (what is observed). optional roles: kartf (observer). effects: none — pure observation of existing state; purity: pure, always. gaRa 1 (BvAdi)",
        aliases: &["view", "inspect"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_SRU",
        slp1: "Sru",
        iast: "śru",
        devanagari: "श्रु",
        category: AtomCategory::Dhatu,
        gloss: "hear",
        semantics: "receive: accept an incoming value or message from an external channel. required role: karman (what is received). optional roles: apAdAna (the sender/channel). effects: input/receipt; purity: impure when the channel is genuinely external (network, user input), pure only in a degenerate/testing sense. gaRa cited as 5 (svAdi) in this registry, though docs/sanskrit-lexicon-verification.md and panini/research/dhatupatha-verification.md both flag the primary Dhatupatha (Sru\\, 01.1092) actually shows gaRa 1 (BvAdi) for this root — an open discrepancy neither project has resolved yet, noted here rather than silently picking one",
        aliases: &["receive", "listen"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_VAC",
        slp1: "vac",
        iast: "vac",
        devanagari: "वच्",
        category: AtomCategory::Dhatu,
        gloss: "say",
        semantics: "express: emit a value as output or declare a statement. required role: karman (what is said). optional roles: kartf (speaker), sampradAna (listener/recipient of the output). effects: output/emission; purity: context dependent per SANSKRIT-P1-DESIGN-DECISIONS's ruling — shares this dhAtu family with write-to-string (pure, no I/O) and print (impure, displays to a user), distinguished by context/purity metadata, not by separate roots. gaRa 2 (adAdi)",
        aliases: &["say", "print", "write-to-string"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_LIKH",
        slp1: "liK",
        iast: "likh",
        devanagari: "लिख्",
        category: AtomCategory::Dhatu,
        gloss: "write",
        semantics: "inscribe: persist a value into a durable medium. required role: karman (what is written). optional roles: kartf (writer), aDikaraRa (the medium/location written to). effects: mutation of durable state; purity: impure, always — inscription is inherently side-effecting, unlike vac's context-dependent purity. gaRa 6 (tudAdi)",
        aliases: &["write-file", "persist"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_PATH",
        slp1: "paW",
        iast: "paṭh",
        devanagari: "पठ्",
        category: AtomCategory::Dhatu,
        gloss: "read",
        semantics: "retrieve: obtain a value from a durable medium or external source (contrast dfS, pure observation of a value already in hand). required role: karman (what is read) or aDikaraRa (the source read from). effects: retrieval, possibly I/O; purity: context dependent — pure if the source is immutable/already-materialized, impure if the source is external/mutable (a file, a stream). gaRa 1 (BvAdi)",
        aliases: &["read-file", "load"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_STHA",
        slp1: "sTA",
        iast: "sthā",
        devanagari: "स्था",
        category: AtomCategory::Dhatu,
        gloss: "stand",
        semantics: "persist-in-place: an entity continues to exist/hold at a given location or in a given state, without being transferred or transformed (contrast gam, a transition away from where something is). required role: kartf (what stands/persists) or aDikaraRa (where it stands). effects: none beyond asserting continued existence; purity: pure as an assertion, though the binding it describes may itself be mutable elsewhere. gaRa 1 (BvAdi)",
        aliases: &["persist-at", "resident"],
        status: AtomStatus::Experimental,
    },
    // -- Kāraka: the six Pāṇinian semantic roles (spec §5), added in
    // SANSKRIT-P4-KARAKA-LAYER. Sūtra citations (P.1.4.24/32/42/45/49/54)
    // and defining wording verified against KARAKA-REFERENCE.md, itself
    // re-checked 2026-08-12 against the Aṣṭādhyāyī per the SANSKRIT-P2
    // ethos (see docs/sanskrit-lexicon-verification.md, which independently
    // confirmed all six sūtra citations against external sources before
    // this task ran). These are ROLES, not actions — `semantics` here
    // states each role's defining test and default vibhakti, not an
    // operational effect the way a dhātu's does.
    Atom {
        id: "KARAKA_KARTR",
        slp1: "kartf",
        iast: "kartṛ",
        devanagari: "कर्तृ",
        category: AtomCategory::Karaka,
        gloss: "agent",
        semantics: "the independent participant (P.1.4.54 svatantraH kartA): whichever participant the speaker treats as the autonomous initiator of the action, not derived from any other role. Default vibhakti: prathamA (nominative) in the active voice; instrumental in the passive (kartR surfaces as instrumental under karmaRi prayoga, the role label itself does not change). This is the default/fallback role -- assigned only when a participant matches no more specific kAraka (spec's own ordering: apAdAna, sampradAna, karaRa, aDikaraRa, karman all take precedence; kartf is last per P.1.4.54's own position as the final rule in the kAraka section)",
        aliases: &["agent", "actor"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "KARAKA_KARMAN",
        slp1: "karman",
        iast: "karman",
        devanagari: "कर्मन्",
        category: AtomCategory::Karaka,
        gloss: "object",
        semantics: "what the agent most wishes to attain through the action (P.1.4.49 kartur IpsitatamaM karma). Default vibhakti: dvitIyA (accusative); becomes the nominative subject under karmaRi prayoga (passive) -- the role label is unchanged by voice, only the surface case and verb agreement shift. A genitive nominal is explicitly never a kAraka at all (possession is outside the kAraka system) and must not be lowered to this role",
        aliases: &["object", "patient"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "KARAKA_KARANA",
        slp1: "karaRa",
        iast: "karaṇa",
        devanagari: "करण",
        category: AtomCategory::Karaka,
        gloss: "instrument",
        semantics: "the most effective means by which the action is accomplished (P.1.4.42 sADakatamaM karaRam) -- 'most effective' is load-bearing: among several things instrumental to an action, only the single most direct means takes this role, not every contributing factor. Default vibhakti: tRtIyA (instrumental)",
        aliases: &["instrument", "means"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "KARAKA_SAMPRADANA",
        slp1: "sampradAna",
        iast: "sampradāna",
        devanagari: "सम्प्रदान",
        category: AtomCategory::Karaka,
        gloss: "recipient",
        semantics: "the one the agent intends to be reached by the object of a giving/directed action (P.1.4.32 karmaRA yam abhipraiti sa sampradAnam). Default vibhakti: caturthI (dative). The spec's own worked example role for dA's third argument: (dA :kartf server :karman packet :sampradAna client)",
        aliases: &["recipient", "beneficiary"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "KARAKA_APADANA",
        slp1: "apAdAna",
        iast: "apādāna",
        devanagari: "अपादान",
        category: AtomCategory::Karaka,
        gloss: "source",
        semantics: "the fixed point from which departure/separation takes place (P.1.4.24 Dhruvam apAye 'pAdAnam) -- 'fixed' is load-bearing: it is the stationary reference point of the separation, not whatever happens to be moving. Default vibhakti: paYcamI (ablative)",
        aliases: &["source", "origin"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "KARAKA_ADHIKARANA",
        slp1: "aDikaraRa",
        iast: "adhikaraṇa",
        devanagari: "अधिकरण",
        category: AtomCategory::Karaka,
        gloss: "locus",
        semantics: "the substratum/locus in or on which the action takes place (P.1.4.45 ADAro 'DikaraRam). Default vibhakti: saptamI (locative)",
        aliases: &["locus", "location"],
        status: AtomStatus::Experimental,
    },
    Atom {
        id: "DHATU_BHU",
        slp1: "BU",
        iast: "bhū",
        devanagari: "भू",
        category: AtomCategory::Dhatu,
        gloss: "become",
        semantics: "come into being: an entity transitions into existence or into a new fundamental nature (contrast kf, which is agent-driven construction of something else; BU is the entity's own transition into being). required role: kartf (what becomes). optional roles: karaRa (the means by which it becomes, if any). effects: existence/state transition; purity: pure when describing a value's nature (e.g. a type coercion), impure when triggering actual allocation/initialization of external state. gaRa 1 (BvAdi) — panini/registry/dhatu/BU.yaml's own gaRa/code (01.0001) is the one exact match found directly in the primary Dhatupatha among all 12 roots here, per docs/sanskrit-lexicon-verification.md",
        aliases: &["become", "coerce-to"],
        status: AtomStatus::Experimental,
    },
];

pub fn by_id(id: &str) -> Option<&'static Atom> {
    REGISTRY.iter().find(|a| a.id == id)
}

pub fn by_slp1(slp1: &str) -> Option<&'static Atom> {
    REGISTRY.iter().find(|a| a.slp1 == slp1)
}

pub fn by_alias(alias: &str) -> Option<&'static Atom> {
    REGISTRY.iter().find(|a| a.aliases.contains(&alias))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::devanagari::slp1_to_devanagari;
    use crate::transliteration::slp1_to_iast;

    #[test]
    fn no_atom_id_equals_its_own_slp1_spelling() {
        // Spec §3's explicit correct/incorrect example: DHATU_DA -> dA is
        // correct; identity == "dA" is not. Mechanically enforced.
        for atom in REGISTRY {
            assert_ne!(
                atom.id, atom.slp1,
                "atom {} must not use its SLP1 spelling as its identity",
                atom.id
            );
        }
    }

    #[test]
    fn registry_ids_are_unique() {
        let mut ids: Vec<&str> = REGISTRY.iter().map(|a| a.id).collect();
        ids.sort();
        let mut deduped = ids.clone();
        deduped.dedup();
        assert_eq!(ids, deduped, "duplicate atom id in registry");
    }

    #[test]
    fn every_atom_iast_field_matches_the_phase_1_transliteration_table() {
        // Prevents the registry's hand-written `iast` field from silently
        // drifting away from the verified Phase 1 table.
        for atom in REGISTRY {
            let computed = slp1_to_iast(atom.slp1).unwrap_or_else(|e| {
                panic!("atom {} has invalid SLP1 `{}`: {e}", atom.id, atom.slp1)
            });
            assert_eq!(
                atom.iast, computed,
                "atom {}'s stored IAST doesn't match Phase 1 transliteration of its SLP1 spelling",
                atom.id
            );
        }
    }

    #[test]
    fn every_atom_devanagari_field_matches_the_phase_2_devanagari_table() {
        // Same drift-prevention as the IAST test, for the Devanagari
        // field added in SANSKRIT-P2-DEVANAGARI-MAPPING.
        for atom in REGISTRY {
            let computed = slp1_to_devanagari(atom.slp1).unwrap_or_else(|e| {
                panic!("atom {} has invalid SLP1 `{}`: {e}", atom.id, atom.slp1)
            });
            assert_eq!(atom.devanagari, computed, "atom {}'s stored Devanagari doesn't match Phase 2 transliteration of its SLP1 spelling", atom.id);
        }
    }

    #[test]
    fn registry_has_all_twelve_spec_dhatu_candidates() {
        // Spec §4's exact candidate list -- this test fails loudly if a
        // future edit accidentally drops one rather than silently
        // shrinking the core.
        let expected_slp1 = [
            "kf", "gam", "dA", "grah", "jYA", "dfS", "Sru", "vac", "liK", "paW", "sTA", "BU",
        ];
        for slp1 in expected_slp1 {
            assert!(
                by_slp1(slp1).is_some(),
                "spec §4 dhatu `{slp1}` is missing from the registry"
            );
        }
        let dhatu_count = REGISTRY
            .iter()
            .filter(|a| a.category == AtomCategory::Dhatu)
            .count();
        assert_eq!(
            dhatu_count, 12,
            "expected exactly the 12-dhatu core (spec §4), found {dhatu_count}"
        );
    }

    #[test]
    fn registry_has_all_six_spec_karaka_roles() {
        let expected_slp1 = [
            "kartf",
            "karman",
            "karaRa",
            "sampradAna",
            "apAdAna",
            "aDikaraRa",
        ];
        for slp1 in expected_slp1 {
            assert!(
                by_slp1(slp1).is_some(),
                "spec §5 kāraka `{slp1}` is missing from the registry"
            );
        }
        let karaka_count = REGISTRY
            .iter()
            .filter(|a| a.category == AtomCategory::Karaka)
            .count();
        assert_eq!(
            karaka_count, 6,
            "expected exactly the six kāraka roles (spec §5), found {karaka_count}"
        );
    }

    #[test]
    fn spec_worked_example_dhatu_da_is_registered_correctly() {
        let atom = by_id("DHATU_DA")
            .expect("DHATU_DA must be in the registry — it's the spec's own worked example");
        assert_eq!(atom.slp1, "dA");
        assert_eq!(atom.iast, "dā");
        assert_eq!(atom.devanagari, "दा");
        assert_eq!(atom.category, AtomCategory::Dhatu);
    }

    #[test]
    fn lookup_by_slp1_and_by_alias_agree_with_lookup_by_id() {
        let by_id_result = by_id("DHATU_DA").unwrap();
        let by_slp1_result = by_slp1("dA").unwrap();
        let by_alias_result = by_alias("give").unwrap();
        assert_eq!(by_id_result.id, by_slp1_result.id);
        assert_eq!(by_id_result.id, by_alias_result.id);
    }

    #[test]
    fn unknown_lookups_return_none() {
        assert!(by_id("DHATU_NONEXISTENT").is_none());
        assert!(by_slp1("zzz").is_none());
        assert!(by_alias("nonexistent-alias").is_none());
    }
}
