//! Standalone Datalog engine for WSM.
//!
//! Цей крейт реалізує незалежний Datalog-двигун: відношення, факти, правила,
//! змінні підстановки, наївний і напівнаївний fixpoint-оцінювач, а також
//! окреме зберігання походження (provenance) від існування кортежів.
//!
//! The kernel deliberately contains no Lisp semantics; it owns only the
//! relational / fixpoint machinery.

use std::collections::{HashMap, HashSet};

/// A ground value that may appear in a tuple.
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum Value {
    /// Symbolic constant, e.g. an entity name or relation tag.
    Symbol(String),
    /// Integer constant.
    Int(i64),
}

impl Value {
    /// Build a symbol value.
    pub fn sym(s: &str) -> Self {
        Value::Symbol(s.to_string())
    }

    /// Build an integer value.
    pub fn int(i: i64) -> Self {
        Value::Int(i)
    }
}

/// A tuple of ground values.
pub type Tuple = Vec<Value>;

/// A term inside an atom: either a constant or a variable.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Term {
    Const(Value),
    Var(String),
}

impl Term {
    /// Shorthand for a constant term.
    pub fn c(v: Value) -> Self {
        Term::Const(v)
    }

    /// Shorthand for a variable term.
    pub fn v(name: &str) -> Self {
        Term::Var(name.to_string())
    }
}

/// An atom: a relation name applied to a list of terms.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Atom {
    pub relation: String,
    pub terms: Vec<Term>,
}

impl Atom {
    /// Create a new atom.
    pub fn new(relation: &str, terms: Vec<Term>) -> Self {
        Atom {
            relation: relation.to_string(),
            terms,
        }
    }
}

/// A Datalog rule: `head :- body`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Rule {
    /// Stable identifier for provenance and debugging.
    pub id: String,
    pub head: Atom,
    pub body: Vec<Atom>,
}

impl Rule {
    /// Create a rule with an explicit identifier.
    pub fn with_id(id: &str, head: Atom, body: Vec<Atom>) -> Self {
        Rule {
            id: id.to_string(),
            head,
            body,
        }
    }
}

/// A record of how one tuple was derived.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Derivation {
    /// Rule identifier that produced the tuple.
    pub rule_id: String,
    /// Tuples matched by the rule body, in body order.
    pub body_tuples: Vec<(String, Tuple)>,
}

impl Derivation {
    /// Marker derivation for base facts.
    pub fn base() -> Self {
        Derivation {
            rule_id: "__base__".to_string(),
            body_tuples: Vec::new(),
        }
    }
}

/// A mapping from variable names to ground values.
pub type Substitution = HashMap<String, Value>;

/// The database holds both tuple existence and separate provenance.
#[derive(Clone, Debug, Default)]
pub struct Database {
    /// Existence of tuples per relation.
    relations: HashMap<String, HashSet<Tuple>>,
    /// Provenance stored separately, keyed by `(relation, tuple)`.
    derivations: HashMap<(String, Tuple), Vec<Derivation>>,
    /// Delta history by generation. Generation 0 holds base facts. Each
    /// subsequent generation holds tuples derived in that fixpoint round.
    /// Kept separately from `relations` so the final closure can be inspected
    /// independently of how it was reached.
    delta_history: Vec<HashMap<String, HashSet<Tuple>>>,
}

impl Database {
    /// Create an empty database.
    pub fn new() -> Self {
        Database::default()
    }

    /// Assert a base fact. Records tuple existence and a single base
    /// derivation. Duplicate assertions are idempotent: the tuple is present
    /// once and the base derivation is recorded once.
    pub fn add_fact(&mut self, relation: &str, tuple: Tuple) {
        let rel = relation.to_string();
        let is_new = self
            .relations
            .entry(rel.clone())
            .or_default()
            .insert(tuple.clone());

        // Generation 0 is the base-fact generation. Ensure it exists and
        // record this base fact there if it is new.
        if self.delta_history.is_empty() {
            self.delta_history.push(HashMap::new());
        }
        if is_new {
            self.delta_history[0]
                .entry(rel.clone())
                .or_default()
                .insert(tuple.clone());
        }

        // A base fact has exactly one base derivation, regardless of how
        // many times it is asserted.
        let list = self.derivations.entry((rel, tuple)).or_default();
        if !list.iter().any(|d| d.rule_id == "__base__") {
            list.push(Derivation::base());
        }
    }

    /// Return the set of tuples in a relation.
    pub fn relation(&self, name: &str) -> &HashSet<Tuple> {
        static EMPTY: std::sync::OnceLock<HashSet<Tuple>> = std::sync::OnceLock::new();
        self.relations
            .get(name)
            .unwrap_or_else(|| EMPTY.get_or_init(HashSet::new))
    }

    /// Return all recorded derivations for a given tuple.
    pub fn derivations(&self, relation: &str, tuple: &Tuple) -> &[Derivation] {
        static EMPTY: std::sync::OnceLock<Vec<Derivation>> = std::sync::OnceLock::new();
        self.derivations
            .get(&(relation.to_string(), tuple.clone()))
            .map(|v| v.as_slice())
            .unwrap_or_else(|| EMPTY.get_or_init(Vec::new).as_slice())
    }

    /// All relation names currently populated.
    pub fn relation_names(&self) -> impl Iterator<Item = &String> {
        self.relations.keys()
    }

    /// The number of fixpoint generations recorded, including generation 0
    /// (base facts).
    pub fn generation_count(&self) -> usize {
        self.delta_history.len()
    }

    /// Return the delta for a given generation. Generation 0 is base facts.
    pub fn generation(&self, index: usize) -> Option<&HashMap<String, HashSet<Tuple>>> {
        self.delta_history.get(index)
    }

    /// Iterate over all recorded generations.
    pub fn generations(&self) -> impl Iterator<Item = (usize, &HashMap<String, HashSet<Tuple>>)> {
        self.delta_history.iter().enumerate()
    }
}

/// A Datalog program is a collection of rules.
#[derive(Clone, Debug, Default)]
pub struct Program {
    rules: Vec<Rule>,
}

impl Program {
    /// Create an empty program.
    pub fn new() -> Self {
        Program::default()
    }

    /// Add a rule to the program.
    pub fn add_rule(&mut self, rule: Rule) -> &mut Self {
        self.rules.push(rule);
        self
    }

    /// Iterate over the rules.
    pub fn rules(&self) -> &[Rule] {
        &self.rules
    }
}

/// Try to extend `substitution` so that `atom` matches `tuple`.
fn unify_atom_with_tuple(
    atom: &Atom,
    tuple: &[Value],
    substitution: &Substitution,
) -> Option<Substitution> {
    if atom.terms.len() != tuple.len() {
        return None;
    }
    let mut sub = substitution.clone();
    for (term, value) in atom.terms.iter().zip(tuple.iter()) {
        match term {
            Term::Const(c) => {
                if c != value {
                    return None;
                }
            }
            Term::Var(name) => match sub.get(name) {
                Some(existing) => {
                    if existing != value {
                        return None;
                    }
                }
                None => {
                    sub.insert(name.clone(), value.clone());
                }
            },
        }
    }
    Some(sub)
}

/// Apply a complete substitution to an atom, producing a ground tuple.
fn apply_substitution(atom: &Atom, substitution: &Substitution) -> Option<Tuple> {
    atom.terms
        .iter()
        .map(|term| match term {
            Term::Const(v) => Some(v.clone()),
            Term::Var(name) => substitution.get(name).cloned(),
        })
        .collect()
}

/// Evaluate a rule against the full database (naive step).
fn eval_rule_naive(
    rule: &Rule,
    relations: &HashMap<String, HashSet<Tuple>>,
) -> Vec<(Substitution, Vec<(String, Tuple)>)> {
    let mut states: Vec<(Substitution, Vec<(String, Tuple)>)> =
        vec![(Substitution::new(), Vec::new())];

    for atom in &rule.body {
        let mut next_states = Vec::new();
        let tuples: Vec<&Tuple> = relations
            .get(&atom.relation)
            .into_iter()
            .flat_map(|s| s.iter())
            .collect();
        for (sub, matches) in states {
            for tuple in &tuples {
                if let Some(new_sub) = unify_atom_with_tuple(atom, tuple, &sub) {
                    let mut new_matches = matches.clone();
                    new_matches.push((atom.relation.clone(), (*tuple).clone()));
                    next_states.push((new_sub, new_matches));
                }
            }
        }
        states = next_states;
    }

    states
}

/// Evaluate a rule with `body[delta_index]` restricted to `delta`, all other
/// body atoms restricted to `relations`.
fn eval_rule_semi_naive(
    rule: &Rule,
    delta_index: usize,
    relations: &HashMap<String, HashSet<Tuple>>,
    delta: &HashMap<String, HashSet<Tuple>>,
) -> Vec<(Substitution, Vec<(String, Tuple)>)> {
    let mut states: Vec<(Substitution, Vec<(String, Tuple)>)> =
        vec![(Substitution::new(), Vec::new())];

    for (idx, atom) in rule.body.iter().enumerate() {
        let mut next_states = Vec::new();
        let source = if idx == delta_index { delta } else { relations };
        let tuples: Vec<&Tuple> = source
            .get(&atom.relation)
            .into_iter()
            .flat_map(|s| s.iter())
            .collect();
        for (sub, matches) in states {
            for tuple in &tuples {
                if let Some(new_sub) = unify_atom_with_tuple(atom, tuple, &sub) {
                    let mut new_matches = matches.clone();
                    new_matches.push((atom.relation.clone(), (*tuple).clone()));
                    next_states.push((new_sub, new_matches));
                }
            }
        }
        states = next_states;
    }

    states
}

/// Public evaluators.
pub struct Evaluator;

impl Evaluator {
    /// Naive fixpoint: repeatedly evaluate all rules over the full database
    /// until no new tuples appear. Derivations are preserved. Each iteration
    /// is recorded as a new generation in `db.delta_history`.
    pub fn naive_fixpoint(program: &Program, db: &mut Database) {
        // Ensure generation 0 exists for base facts.
        if db.delta_history.is_empty() {
            db.delta_history.push(HashMap::new());
        }

        loop {
            let mut new_tuples: HashMap<String, HashSet<Tuple>> = HashMap::new();
            let mut new_derivations: Vec<((String, Tuple), Derivation)> = Vec::new();

            for rule in program.rules() {
                let results = eval_rule_naive(rule, &db.relations);
                for (sub, body_matches) in results {
                    if let Some(head_tuple) = apply_substitution(&rule.head, &sub) {
                        let rel = rule.head.relation.clone();
                        let key = (rel.clone(), head_tuple.clone());
                        let derivation = Derivation {
                            rule_id: rule.id.clone(),
                            body_tuples: body_matches,
                        };
                        new_derivations.push((key.clone(), derivation));
                        new_tuples.entry(rel).or_default().insert(head_tuple);
                    }
                }
            }

            Self::record_derivations(&mut db.derivations, new_derivations);

            let mut generation_delta: HashMap<String, HashSet<Tuple>> = HashMap::new();
            let mut added = false;
            for (rel, tuples) in new_tuples {
                let set = db.relations.entry(rel.clone()).or_default();
                for tuple in tuples {
                    if set.insert(tuple.clone()) {
                        generation_delta
                            .entry(rel.clone())
                            .or_default()
                            .insert(tuple);
                        added = true;
                    }
                }
            }

            if !added {
                break;
            }
            db.delta_history.push(generation_delta);
        }
    }

    /// Semi-naive fixpoint: each iteration uses the previous iteration's
    /// delta for at least one body atom, with remaining atoms matched against
    /// the full database. Derivations are preserved. Each iteration is
    /// recorded as a new generation in `db.delta_history`.
    pub fn semi_naive_fixpoint(program: &Program, db: &mut Database) {
        // Ensure generation 0 exists for base facts.
        if db.delta_history.is_empty() {
            db.delta_history.push(HashMap::new());
        }

        // The initial delta is the set of base facts already in the database.
        let mut delta: HashMap<String, HashSet<Tuple>> = db.relations.clone();

        if delta.values().all(|s| s.is_empty()) {
            return;
        }

        loop {
            let mut delta_new: HashMap<String, HashSet<Tuple>> = HashMap::new();
            let mut new_derivations: Vec<((String, Tuple), Derivation)> = Vec::new();

            for rule in program.rules() {
                for delta_index in 0..rule.body.len() {
                    let results = eval_rule_semi_naive(rule, delta_index, &db.relations, &delta);
                    for (sub, body_matches) in results {
                        if let Some(head_tuple) = apply_substitution(&rule.head, &sub) {
                            let rel = rule.head.relation.clone();
                            let key = (rel.clone(), head_tuple.clone());
                            let derivation = Derivation {
                                rule_id: rule.id.clone(),
                                body_tuples: body_matches,
                            };
                            new_derivations.push((key.clone(), derivation));

                            let already_known = db
                                .relations
                                .get(&rel)
                                .map(|s| s.contains(&head_tuple))
                                .unwrap_or(false);
                            if !already_known {
                                delta_new.entry(rel).or_default().insert(head_tuple);
                            }
                        }
                    }
                }
            }

            Self::record_derivations(&mut db.derivations, new_derivations);

            let mut added = false;
            for (rel, tuples) in &delta_new {
                let set = db.relations.entry(rel.clone()).or_default();
                for tuple in tuples {
                    set.insert(tuple.clone());
                }
                added = true;
            }

            if !added {
                break;
            }
            db.delta_history.push(delta_new.clone());
            delta = delta_new;
        }
    }

    fn record_derivations(
        derivations: &mut HashMap<(String, Tuple), Vec<Derivation>>,
        new: Vec<((String, Tuple), Derivation)>,
    ) {
        for (key, derivation) in new {
            let list = derivations.entry(key).or_default();
            if !list.contains(&derivation) {
                list.push(derivation);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fact(db: &mut Database, relation: &str, tuple: Tuple) {
        db.add_fact(relation, tuple);
    }

    #[test]
    fn base_facts_exist() {
        let mut db = Database::new();
        db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
        assert!(
            db.relation("edge")
                .contains(&vec![Value::int(1), Value::int(2)])
        );
        assert_eq!(
            db.derivations("edge", &vec![Value::int(1), Value::int(2)])
                .len(),
            1
        );
    }

    #[test]
    fn duplicate_base_fact_keeps_single_derivation() {
        let mut db = Database::new();
        db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
        db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
        // Tuple existence is idempotent.
        assert_eq!(db.relation("edge").len(), 1);
        // A base fact has exactly one base derivation, even if asserted twice.
        let derivations = db.derivations("edge", &vec![Value::int(1), Value::int(2)]);
        assert_eq!(derivations.len(), 1);
        assert_eq!(derivations[0].rule_id, "__base__");
    }

    #[test]
    fn transitive_closure_naive() {
        let mut db = Database::new();
        fact(&mut db, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db, "edge", vec![Value::int(2), Value::int(3)]);
        fact(&mut db, "edge", vec![Value::int(3), Value::int(4)]);

        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "path-base",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
        ));
        program.add_rule(Rule::with_id(
            "path-rec",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![
                Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
                Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
            ],
        ));

        Evaluator::naive_fixpoint(&program, &mut db);

        let path = db.relation("path");
        assert_eq!(path.len(), 6);
        assert!(path.contains(&vec![Value::int(1), Value::int(2)]));
        assert!(path.contains(&vec![Value::int(1), Value::int(3)]));
        assert!(path.contains(&vec![Value::int(1), Value::int(4)]));
        assert!(path.contains(&vec![Value::int(2), Value::int(3)]));
        assert!(path.contains(&vec![Value::int(2), Value::int(4)]));
        assert!(path.contains(&vec![Value::int(3), Value::int(4)]));
    }

    #[test]
    fn transitive_closure_semi_naive() {
        let mut db = Database::new();
        fact(&mut db, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db, "edge", vec![Value::int(2), Value::int(3)]);
        fact(&mut db, "edge", vec![Value::int(3), Value::int(4)]);

        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "path-base",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
        ));
        program.add_rule(Rule::with_id(
            "path-rec",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![
                Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
                Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
            ],
        ));

        Evaluator::semi_naive_fixpoint(&program, &mut db);

        let path = db.relation("path");
        assert_eq!(path.len(), 6);
        assert!(path.contains(&vec![Value::int(1), Value::int(4)]));
    }

    #[test]
    fn naive_equals_semi_naive_closure() {
        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "path-base",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
        ));
        program.add_rule(Rule::with_id(
            "path-rec",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![
                Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
                Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
            ],
        ));

        let mut db_naive = Database::new();
        fact(&mut db_naive, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db_naive, "edge", vec![Value::int(2), Value::int(3)]);
        fact(&mut db_naive, "edge", vec![Value::int(3), Value::int(4)]);
        fact(&mut db_naive, "edge", vec![Value::int(4), Value::int(5)]);
        Evaluator::naive_fixpoint(&program, &mut db_naive);

        let mut db_sn = Database::new();
        fact(&mut db_sn, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db_sn, "edge", vec![Value::int(2), Value::int(3)]);
        fact(&mut db_sn, "edge", vec![Value::int(3), Value::int(4)]);
        fact(&mut db_sn, "edge", vec![Value::int(4), Value::int(5)]);
        Evaluator::semi_naive_fixpoint(&program, &mut db_sn);

        assert_eq!(db_naive.relation("path"), db_sn.relation("path"));
    }

    #[test]
    fn base_facts_are_generation_zero() {
        let mut db = Database::new();
        db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
        db.add_fact("edge", vec![Value::int(2), Value::int(3)]);

        assert_eq!(db.generation_count(), 1);
        let gen0 = db.generation(0).unwrap();
        assert_eq!(gen0.get("edge").unwrap().len(), 2);
    }

    #[test]
    fn naive_fixpoint_records_generation_history() {
        let mut db = Database::new();
        fact(&mut db, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db, "edge", vec![Value::int(2), Value::int(3)]);
        fact(&mut db, "edge", vec![Value::int(3), Value::int(4)]);

        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "path-base",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
        ));
        program.add_rule(Rule::with_id(
            "path-rec",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![
                Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
                Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
            ],
        ));

        Evaluator::naive_fixpoint(&program, &mut db);

        // Gen 0: base edge facts.
        // Gen 1: path(1,2), path(2,3), path(3,4) from path-base.
        // Gen 2: path(1,3), path(2,4) from path-rec over gen 1.
        // Gen 3: path(1,4) from path-rec over gen 2.
        assert_eq!(db.generation_count(), 4);

        let gen1 = db.generation(1).unwrap();
        assert_eq!(gen1.get("path").unwrap().len(), 3);

        let gen3 = db.generation(3).unwrap();
        assert!(
            gen3.get("path")
                .unwrap()
                .contains(&vec![Value::int(1), Value::int(4)])
        );
    }

    #[test]
    fn semi_naive_fixpoint_records_generation_history() {
        let mut db = Database::new();
        fact(&mut db, "edge", vec![Value::int(1), Value::int(2)]);
        fact(&mut db, "edge", vec![Value::int(2), Value::int(3)]);

        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "path-base",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
        ));
        program.add_rule(Rule::with_id(
            "path-rec",
            Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
            vec![
                Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
                Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
            ],
        ));

        Evaluator::semi_naive_fixpoint(&program, &mut db);

        assert!(db.generation_count() >= 2);
        // Generation 0 is base facts.
        assert!(db.generation(0).unwrap().get("edge").is_some());
        // Later generations contain derived path tuples.
        let derived: usize = db
            .generations()
            .skip(1)
            .map(|(_, g)| g.get("path").map(|s| s.len()).unwrap_or(0))
            .sum();
        assert_eq!(derived, 3);
    }

    #[test]
    fn tuple_with_two_independent_derivations_is_preserved() {
        // q can be derived from either p or r.
        let mut db = Database::new();
        fact(&mut db, "p", vec![Value::sym("a")]);
        fact(&mut db, "r", vec![Value::sym("a")]);

        let mut program = Program::new();
        program.add_rule(Rule::with_id(
            "q-from-p",
            Atom::new("q", vec![Term::v("X")]),
            vec![Atom::new("p", vec![Term::v("X")])],
        ));
        program.add_rule(Rule::with_id(
            "q-from-r",
            Atom::new("q", vec![Term::v("X")]),
            vec![Atom::new("r", vec![Term::v("X")])],
        ));

        Evaluator::naive_fixpoint(&program, &mut db);

        let q = db.relation("q");
        assert_eq!(q.len(), 1);
        let tuple = vec![Value::sym("a")];
        assert!(q.contains(&tuple));

        let derivations = db.derivations("q", &tuple);
        assert_eq!(
            derivations.len(),
            2,
            "both independent derivations must be preserved"
        );
        let ids: HashSet<_> = derivations.iter().map(|d| d.rule_id.as_str()).collect();
        assert!(ids.contains("q-from-p"));
        assert!(ids.contains("q-from-r"));
    }
}
