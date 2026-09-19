use crate::bignum::BigInt;
use crate::{Environment, Exactness, Expr};
use std::{
    cell::RefCell, cmp::Ordering, fmt, net::TcpListener, net::TcpStream, ops::Neg, rc::Rc,
    str::FromStr,
};

/// A reduced exact fraction owned by the language runtime, backed by the
/// hand-rolled `BigInt` in `bignum.rs` — "exact" has no numeric ceiling
/// short of available memory. Rust does this low-level numeric algorithm,
/// the same way it already did the bounded `i64` version this replaced;
/// my-lisp itself never grows an arithmetic primitive (see
/// docs/language-core.md). `denominator` is always positive and the
/// fraction always reduced — the invariant `from_big` maintains on every
/// construction path.
/// Skorochenyi tochnyi drib, yakym volodiie runtime movy, na osnovi vlasnoruch
/// napysanoho `BigInt` u `bignum.rs` — "tochnyi" ne maie chyslovoi steli,
/// okrim dostupnoi pamiati. Rust robyt tsei nyzkorivnevyi chyslovyi
/// alhorytm tak samo, yak uzhe robyv obmezhenu `i64`-versiiu, yaku tse zaminylo;
/// sama my-lisp nikoly ne rozshyriuie aryfmetychnyi prymityv (dyv.
/// docs/language-core.md). `denominator` zavzhdy dodatnyi, a drib zavzhdy
/// skorochenyi — invariant, yakyi `from_big` pidtrymuie na kozhnomu shliakhu
/// pobudovy.
/// Ein gekürzter exakter Bruch im Besitz der Sprachlaufzeit, basierend auf
/// dem von Hand geschriebenen `BigInt` in `bignum.rs` — "exakt" hat keine
/// numerische Obergrenze außer dem verfügbaren Speicher. Rust erledigt
/// diesen Low-Level-Zahlenalgorithmus, genauso wie es bereits die
/// begrenzte `i64`-Version tat, die dies ersetzt; my-lisp selbst erweitert
/// nie ein arithmetisches Primitiv (siehe docs/language-core.md).
/// `denominator` ist immer positiv und der Bruch immer gekürzt — die
/// Invariante, die `from_big` bei jedem Konstruktionspfad aufrechterhält.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Rational {
    numerator: BigInt,
    denominator: BigInt,
}

/// Why a decimal literal didn't become a `Rational` — a typed failure so the
/// reader never has to guess between "this isn't a number" and "this is a
/// number we refused to build." The distinction matters because the two are
/// observably different per S2/S3: the first is an ordinary symbol, the second
/// must be a *named* failure, never a silent relabeling of a valid literal.
/// Chomu desiatkovyi literal ne stav `Rational` — typizovanyi proval, shchob
/// reader nikoly ne vhaduvav mizh "tse ne chyslo" i "tse chyslo, yake my
/// vidmovylys buduvaty." Rozriznennia vazhlyve, bo tsi dva vypadky sposterezhu-
/// vano rizni za S2/S3: pershyi — zvychainyi symvol, druhyi — *nazvanyi*
/// proval, nikoly ne movchazne perekvalifikuvannia validnoho literala.
/// Warum ein Dezimal-Literal kein `Rational` wurde — ein typisierter Fehler,
/// damit der Reader nie raten muss zwischen "das ist keine Zahl" und "das ist
/// eine Zahl, die wir zu bauen abgelehnt haben." Die Unterscheidung zählt,
/// denn die beiden Fälle sind laut S2/S3 beobachtbar verschieden: ersteres ist
/// ein gewöhnliches Symbol, letzteres ein *benannter* Fehler, niemals eine
/// stille Umbenennung eines gültigen Literals.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DecimalLiteralError {
    /// The token is not a well-formed decimal/exponential literal at all
    /// (`.`, `1e`, `1e+`, `1e-`, `1.2.3`, `1ee3`, `--0.5`) — the reader keeps
    /// the current behavior and treats it as an ordinary symbol.
    /// Token vzahali ne ye korektnym desiatkovym/eksponentsiinym literalom
    /// (`.`, `1e`, `1e+`, `1e-`, `1.2.3`, `1ee3`, `--0.5`) — reader zberihaie
    /// potochnu povedinku y traktuie yoho yak zvychainyi symvol.
    /// Das Token ist überhaupt kein wohlgeformtes Dezimal-/Exponential-Literal
    /// (`.`, `1e`, `1e+`, `1e-`, `1.2.3`, `1ee3`, `--0.5`) — der Reader behält
    /// das bisherige Verhalten bei und behandelt es als gewöhnliches Symbol.
    InvalidSyntax,
    /// The token is a syntactically valid decimal literal, but constructing it
    /// would exceed a parser resource limit (an exponent magnitude beyond the
    /// hardcoded ±10000 cap that bounds the `10^N` digit-string allocation).
    /// This is the S3-shaped case: the limit must fail *named* (`NumericOverflow`),
    /// never silently turn a valid numeric literal into an identifier.
    /// Token — syntaksychno korektnyi desiatkovyi literal, ale yoho pobudova
    /// perevyshchyla b resursnu mezhu parsera (velychyna eksponenty ponad
    /// zakladenu mezhu ±10000, yaka obmezhuie alokatsiiu tsyfrovoi riadky `10^N`).
    /// Tse vypadok formy S3: mezha musi provaliuvatys *nazvano* (`NumericOverflow`),
    /// nikoly ne peretvoriuvaty movchky validnyi chyslovyi literal na identyfikator.
    /// Das Token ist ein syntaktisch gültiges Dezimal-Literal, aber seine
    /// Konstruktion würde eine Parser-Ressourcengrenze überschreiten (eine
    /// Exponentengröße jenseits der hartkodierten ±10000-Grenze, die die
    /// Ziffernstring-Allokation von `10^N` begrenzt). Das ist der S3-Fall: Die
    /// Grenze muss *benannt* fehlschlagen (`NumericOverflow`), niemals ein
    /// gültiges numerisches Literal still in einen Bezeichner verwandeln.
    ResourceLimitExceeded,
}

impl PartialOrd for Rational {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Neg for Rational {
    type Output = Self;
    fn neg(self) -> Self {
        Self {
            numerator: self.numerator.neg(),
            denominator: self.denominator,
        }
    }
}

impl Ord for Rational {
    fn cmp(&self, other: &Self) -> Ordering {
        // Denominators are always positive (see `from_big`), so comparing by
        // cross-multiplication is exact — no float involved, no rounding.
        // Znamennyky zavzhdy dodatni (dyv. `from_big`), tozh porivniannia
        // khrest-navkhrest tochne — bez float, bez okruhlennia.
        // Nenner sind immer positiv (siehe `from_big`), daher ist der
        // Vergleich per Kreuzmultiplikation exakt — kein Float, keine Rundung.
        self.numerator
            .mul(&other.denominator)
            .cmp(&other.numerator.mul(&self.denominator))
    }
}

/// R2 (owner-directed, 2026-09-02, follows R1 in commit d7f3118): bounds
/// the decimal digit-count `from_decimal_literal` will ever materialize
/// for a scientific-notation literal's `10^N` multiplier -- exponent
/// *magnitude* is the direct, exact proxy for that digit-count here (an
/// exponent of N means N digits), so bounding one bounds the other with
/// no separate size computation needed. Was ±100_000 -- itself never
/// exercised at the boundary in tests (see `parser.rs`'s
/// `decimal_literals_within_the_resource_limit_still_parse`) because
/// `10^100000`'s GCD reduction is minutes-long; the previous comment
/// there called that boundary value itself "an internal DoS-hedge, not
/// a contract fact" -- exactly the license this lowers it under. Chosen
/// empirically, not guessed: ±10_000 gives a measured worst-case parse of
/// ~0.08s (`crates/wsm-guard-core/examples/profile_reader_scaling.rs`,
/// this session's scratch tool) while staying a 10x margin above every
/// currently-tested legitimate literal (`1e1000`/`1e-1000`/`1.25e1000`/
/// `1.25e-1000`, still comfortably inside the bound). Small enough that,
/// unlike the old ±100_000, the exact boundary itself is now cheap
/// enough to exercise directly in a test.
const MAX_DECIMAL_LITERAL_EXPONENT_MAGNITUDE: i32 = 10_000;

impl Rational {
    pub fn new(numerator: i64, denominator: i64) -> Option<Self> {
        Self::from_big(BigInt::from_i64(numerator), BigInt::from_i64(denominator))
    }

    /// Parses a `numerator/denominator` literal directly as arbitrary-precision
    /// integers, for source tokens too large for `i64` (see `parser.rs`).
    /// Parsyt literal `chyselnyk/znamennyk` napriamu yak tsili dovilnoi
    /// tochnosti, dlia tokeniv kodu, zavelykykh dlia `i64` (dyv. `parser.rs`).
    /// Parst ein `Zähler/Nenner`-Literal direkt als beliebig genaue Ganzzahlen,
    /// für Quelltoken, die zu groß für `i64` sind (siehe `parser.rs`).
    pub fn from_literal(numerator: &str, denominator: &str) -> Option<Self> {
        let numerator = BigInt::from_str(numerator).ok()?;
        let denominator = BigInt::from_str(denominator).ok()?;
        Self::from_big(numerator, denominator)
    }

    /// Parses a decimal literal (like `0.5`, `3.14`, `1e-3`) directly into an exact
    /// arbitrary-precision `Rational`, preserving the full mathematical value
    /// without relying on intermediate floating-point approximations.
    ///
    /// Returns a typed error instead of an untyped `None` so the reader can tell
    /// apart two genuinely different outcomes (see `DecimalLiteralError`): text
    /// that is not a decimal literal at all, versus a syntactically valid literal
    /// the parser refused to build for a resource reason. The second must never
    /// silently degrade into an ordinary symbol (S3) — that would turn a valid
    /// numeric literal into an identifier only because of an internal limit.
    pub fn from_decimal_literal(text: &str) -> Result<Self, DecimalLiteralError> {
        let text = text.to_lowercase();
        let (base_str, exp_str) = if let Some((b, e)) = text.split_once('e') {
            (b, Some(e))
        } else {
            (text.as_str(), None)
        };

        if base_str.matches('.').count() > 1 {
            return Err(DecimalLiteralError::InvalidSyntax);
        }

        let scientific_exp: i32 = if let Some(e) = exp_str {
            let digits = e.strip_prefix(['+', '-']).unwrap_or(e);
            if digits.is_empty() || !digits.chars().all(|c| c.is_ascii_digit()) {
                return Err(DecimalLiteralError::InvalidSyntax);
            }
            e.parse()
                .map_err(|_| DecimalLiteralError::ResourceLimitExceeded)?
        } else {
            0
        };

        let (mantissa_str, decimal_exp) =
            if let Some((int_part, frac_part)) = base_str.split_once('.') {
                let decimal_exp = frac_part.len() as i32;
                let mut m = String::with_capacity(int_part.len() + frac_part.len());
                m.push_str(int_part);
                m.push_str(frac_part);
                (m, decimal_exp)
            } else {
                (base_str.to_string(), 0)
            };

        if mantissa_str.is_empty() || mantissa_str == "-" || mantissa_str == "+" {
            return Err(DecimalLiteralError::InvalidSyntax);
        }

        let mantissa =
            BigInt::from_str(&mantissa_str).map_err(|_| DecimalLiteralError::InvalidSyntax)?;
        let total_exp = scientific_exp
            .checked_sub(decimal_exp)
            .ok_or(DecimalLiteralError::ResourceLimitExceeded)?;

        if !(-MAX_DECIMAL_LITERAL_EXPONENT_MAGNITUDE..=MAX_DECIMAL_LITERAL_EXPONENT_MAGNITUDE)
            .contains(&total_exp)
        {
            return Err(DecimalLiteralError::ResourceLimitExceeded);
        }

        let abs_exp = total_exp.unsigned_abs() as usize;
        let mut multiplier_str = String::with_capacity(abs_exp + 1);
        multiplier_str.push('1');
        multiplier_str.extend(std::iter::repeat_n('0', abs_exp));

        let power_of_10 =
            BigInt::from_str(&multiplier_str).map_err(|_| DecimalLiteralError::InvalidSyntax)?;

        if total_exp >= 0 {
            Self::from_big(mantissa.mul(&power_of_10), BigInt::from_i64(1))
                .ok_or(DecimalLiteralError::InvalidSyntax)
        } else {
            Self::from_big(mantissa, power_of_10).ok_or(DecimalLiteralError::InvalidSyntax)
        }
    }

    fn from_big(numerator: BigInt, denominator: BigInt) -> Option<Self> {
        if denominator.is_zero() {
            return None;
        }
        let (numerator, denominator) = if denominator.is_negative() {
            (numerator.neg(), denominator.neg())
        } else {
            (numerator, denominator)
        };
        let divisor = numerator.gcd(&denominator);
        if divisor.is_zero() {
            // Only when numerator is also zero (gcd(0, d) = d otherwise);
            // 0/d reduces to the canonical 0/1 without a division step.
            return Some(Self {
                numerator: BigInt::zero(),
                denominator: BigInt::from_i64(1),
            });
        }
        let (numerator, _) = numerator.div_rem(&divisor)?;
        let (denominator, _) = denominator.div_rem(&divisor)?;
        Some(Self {
            numerator,
            denominator,
        })
    }

    pub fn integer(value: i64) -> Self {
        Self {
            numerator: BigInt::from_i64(value),
            denominator: BigInt::from_i64(1),
        }
    }

    /// The wider of numerator/denominator bit width — see `BigInt::bit_length`
    /// for why this exists (an opt-in resource-limit check, not ordinary use).
    /// Shyrsha z dvokh velychyn chyselnyka/znamennyka v bitakh — dyv.
    /// `BigInt::bit_length`, chomu tse isnuie (optsiina perevirka obmezhennia
    /// resursu, ne zvychaine vykorystannia).
    pub fn bit_length(&self) -> usize {
        self.numerator
            .bit_length()
            .max(self.denominator.bit_length())
    }

    pub fn checked_div(self, divisor: Self) -> Option<Self> {
        if divisor.numerator.is_zero() {
            return None;
        }
        Self::from_big(
            self.numerator.mul(&divisor.denominator),
            self.denominator.mul(&divisor.numerator),
        )
    }

    pub fn checked_add(self, other: Self) -> Option<Self> {
        let numerator = self
            .numerator
            .mul(&other.denominator)
            .add(&other.numerator.mul(&self.denominator));
        Self::from_big(numerator, self.denominator.mul(&other.denominator))
    }

    pub fn checked_sub(self, other: Self) -> Option<Self> {
        let numerator = self
            .numerator
            .mul(&other.denominator)
            .sub(&other.numerator.mul(&self.denominator));
        Self::from_big(numerator, self.denominator.mul(&other.denominator))
    }

    pub fn checked_mul(self, other: Self) -> Option<Self> {
        Self::from_big(
            self.numerator.mul(&other.numerator),
            self.denominator.mul(&other.denominator),
        )
    }

    pub fn checked_neg(self) -> Option<Self> {
        Some(Self {
            numerator: self.numerator.neg(),
            denominator: self.denominator,
        })
    }

    pub fn as_f64(&self) -> f64 {
        self.numerator.to_f64() / self.denominator.to_f64()
    }

    pub fn is_integer(&self) -> bool {
        self.denominator.to_i64() == Some(1)
    }

    /// `Some(n)` only if this exact value is a whole number *and* representable
    /// as an `i64` within `f64`'s 2^53 exact-integer range — the one case
    /// `crates/my-lisp/src/eval/arithmetic.rs`'s `exact_value` may cosmetically
    /// print through `Value::Number` instead of `Value::Rational` without ever
    /// losing precision doing so. Anything bigger stays `Value::Rational` (see
    /// `Display`, which omits `/1` for whole numbers) rather than risk exactly
    /// the silent-approximation the exact-number principle forbids.
    /// `Some(n)`, lyshe yakshcho tse tsile znachennia *i* vlazyt v `i64` v mezhakh
    /// 2^53-diapazonu tochnykh tsilykh `f64` — yedynyi vypadok, koly `exact_value`
    /// u `crates/my-lisp/src/eval/arithmetic.rs` mozhe kosmetychno drukuvaty
    /// cherez `Value::Number` zamist `Value::Rational`, ne vtrachaiuchy tochnist.
    /// Use bilshe lyshaietsia `Value::Rational` (dyv. `Display`, shcho propuskaie
    /// `/1` dlia tsilykh chysel), a ne ryzykuie same tym tykhym nablyzhenniam, yake
    /// zaboroniaie pryntsyp tochnykh chysel.
    /// `Some(n)` nur, wenn dieser exakte Wert eine ganze Zahl ist *und* als
    /// `i64` innerhalb von `f64`s 2^53-Bereich exakter Ganzzahlen darstellbar
    /// — der eine Fall, in dem `exact_value` in
    /// `crates/my-lisp/src/eval/arithmetic.rs` kosmetisch über `Value::Number`
    /// statt `Value::Rational` drucken darf, ohne dabei Genauigkeit zu
    /// verlieren. Alles Größere bleibt `Value::Rational` (siehe `Display`,
    /// das `/1` bei Ganzzahlen weglässt), statt genau die stille Approximation
    /// zu riskieren, die das Prinzip exakter Zahlen verbietet.
    pub fn as_precise_i64(&self) -> Option<i64> {
        if !self.is_integer() {
            return None;
        }
        const MAX_EXACT: i64 = 1 << 53;
        let value = self.numerator.to_i64()?;
        (-MAX_EXACT..=MAX_EXACT).contains(&value).then_some(value)
    }

    /// FASL support: numerator+denominator limb encoding.
    pub(crate) fn write_fasl(&self, out: &mut Vec<u8>) {
        self.numerator.write_fasl(out);
        self.denominator.write_fasl(out);
    }

    /// FASL inverse of `write_fasl`; None on corruption.
    pub(crate) fn read_fasl(bytes: &[u8], pos: &mut usize) -> Option<Self> {
        let numerator = BigInt::read_fasl(bytes, pos)?;
        let denominator = BigInt::read_fasl(bytes, pos)?;
        Self::from_big(numerator, denominator)
    }

    pub fn is_negative(&self) -> bool {
        self.numerator.is_negative()
    }
}

impl fmt::Display for Rational {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_integer() {
            write!(formatter, "{}", self.numerator)
        } else {
            write!(formatter, "{}/{}", self.numerator, self.denominator)
        }
    }
}

/// A closure keeps executable forms together with their lexical environment.
/// Zamykannia zberihaie vykonuvani formy razom iz yikhnim leksychnym seredovyshchem.
/// Eine Closure bewahrt ausführbare Formen zusammen mit ihrer lexikalischen Umgebung auf.
#[derive(Clone, Debug)]
pub struct Closure {
    pub(crate) parameters: Vec<Rc<str>>,
    /// The dotted-list/bare-symbol rest parameter, if any — bound to a list
    /// of every argument past `parameters.len()`. `None` means the closure
    /// takes exactly `parameters.len()` arguments, no more.
    /// Variatyvnyi parametr (dotted-list/holyi symvol), yakshcho ye — zviazuietsia
    /// zi spyskom usikh arhumentiv ponad `parameters.len()`. `None` oznachaie,
    /// shcho zamykannia pryimaie tochno `parameters.len()` arhumentiv, ne bilshe.
    /// Der variadische Rest-Parameter (Dotted-List/nacktes Symbol), falls
    /// vorhanden — gebunden an eine Liste aller Argumente über
    /// `parameters.len()` hinaus. `None` bedeutet, die Closure nimmt genau
    /// `parameters.len()` Argumente, nicht mehr.
    pub(crate) rest: Option<Rc<str>>,
    pub(crate) body: Rc<[Expr]>,
    pub(crate) environment: Environment,
}

pub type BuiltinFunction =
    Rc<dyn Fn(&[Value], &crate::Environment, crate::Span) -> Result<Value, crate::LanguageError>>;

/// A primitive operation as a first-class value. Contract 2.1 introduced
/// callable builtin values; Contract 6.0 keeps that value-level property while
/// reserving Canon 0+7 *names*. A Canon callable can still be passed as a value,
/// but its registered EN/UK/SA/symbolic spellings cannot be rebound. Non-Canon
/// builtins remain ordinary lexical values. Arguments arrive pre-evaluated;
/// special forms never become Builtins (they are syntax, not values).
/// Prymityv yak pershoklasne znachennia. Kontrakt 6.0 ne zaboraie peredavaty
/// Canon-callable yak znachennia; vin rezervuie lyshe kanonichni imena vid
/// perevyznachennia. Ne-Canon builtiny zalyshaiutsia zvychainymy lexical values.
pub struct Builtin {
    pub name: &'static str,
    pub func: BuiltinFunction,
}

/// Immutable contiguous numeric storage for portable bulk-compute lowering.
#[derive(Clone, Debug)]
pub enum NumericBuffer {
    I32(std::sync::Arc<[i32]>),
    F32(std::sync::Arc<[f32]>),
}

impl PartialEq for NumericBuffer {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::I32(left), Self::I32(right)) => left == right,
            (Self::F32(left), Self::F32(right)) => {
                left.len() == right.len()
                    && left
                        .iter()
                        .zip(right.iter())
                        .all(|(left, right)| left.to_bits() == right.to_bits())
            }
            _ => false,
        }
    }
}

impl std::fmt::Debug for Builtin {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "#<builtin {}>", self.name)
    }
}

/// Runtime data is independent of the parser and any host representation.
/// Dani vykonannia ne zalezhat vid parsera ta predstavlennia u khost-systemi.
/// Laufzeitdaten sind unabhängig vom Parser und von jeder Host-Darstellung.
#[derive(Clone, Debug)]
pub enum Value {
    Nil,
    Bool(bool),
    Number(f64, Exactness),
    Rational(Rational),
    String(Rc<str>),
    Symbol(Rc<str>),
    Pair(Rc<Value>, Rc<Value>),
    Closure(Rc<Closure>),
    Macro(Rc<Closure>),
    /// Opaque one-byte semantic identity as a first-class callable value.
    /// The identity belongs to the language registry, not to a Rust object.
    SemanticRef(u8),
    /// Legacy host implementation closure as a first-class value. This is an
    /// implementation projection, never the language identity key.
    Builtin(std::rc::Rc<Builtin>),
    /// Opaque value supplied by an embedding host. Source syntax cannot
    /// construct this variant, so a Lisp program may retain and pass a handle
    /// but cannot forge a host token.
    HostHandle {
        kind: Rc<str>,
        token: u64,
    },
    /// Persistent vector: O(1) indexed access for numeric workloads
    Vector(std::rc::Rc<std::cell::RefCell<Vec<Value>>>),
    /// Fixed-width immutable numeric data. Unlike `Vector`, this is
    /// homogeneous, contiguous, and has no mutating language operation.
    NumericBuffer(NumericBuffer),
    /// An open TCP connection (PLAN.md item 21) — the outbound-client half
    /// of "talk to other AI systems," principle 3 extended to external
    /// agents/LLM APIs. Opaque host-capability handle, the same category
    /// `read-file`/`write-file` already occupy — not user-visible mutable
    /// *data* in the item-16 sense (nothing here lets a program mutate an
    /// ordinary binding), just a resource the host manages on the
    /// language's behalf. `RefCell` because reading/writing a stream
    /// genuinely advances its position — there is no persistent,
    /// side-effect-free way to model "the next unread byte of a live
    /// network connection."
    /// Vidkryte TCP-ziednannia (PLAN.md, punkt 21) — vykhidna/kliientska
    /// polovyna "spilkuvatys z inshymy AI-systemamy", pryntsyp 3, poshyrenyi
    /// na zovnishnikh ahentiv/LLM API. Neprozoryi handle host-mozhlyvosti, ta
    /// sama katehoriia, shcho vzhe zaimaiut `read-file`/`write-file` — ne
    /// vydyma korystuvachu mutabelna *dani* v sensi item 16 (nishcho tut ne
    /// daie prohrami mutuvaty zvychaine zviazuvannia), lyshe resurs, yakym khost
    /// keruie vid imeni movy. `RefCell`, bo chytannia/zapys u potik spravdi
    /// prosuvaie yoho pozytsiiu — nemaie postiinoho, bez-pobichno-efektnoho
    /// sposobu zmodeliuvaty "nastupnyi neprochytanyi bait zhyvoho merezhevoho
    /// ziednannia".
    TcpConnection(Rc<RefCell<TcpStream>>),
    /// A listening TCP socket (PLAN.md item 21) — the inbound-server half:
    /// lets my-lisp accept connections from other agents, not just call
    /// out to them. No `RefCell` needed — `TcpListener::accept` takes
    /// `&self`, it doesn't need to mutate the listener itself.
    /// TCP-soket, shcho slukhaie (PLAN.md, punkt 21) — vkhidna/serverna
    /// polovyna: dozvoliaie my-lisp pryimaty ziednannia vid inshykh ahentiv, ne
    /// lyshe zvertatys do nykh. `RefCell` ne potriben — `TcpListener::accept`
    /// bere `&self`, ne potrebuie mutuvaty sam listener.
    TcpListener(Rc<TcpListener>),
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Nil, Value::Nil) => true,
            (Value::Bool(left), Value::Bool(right)) => left == right,
            // Exactness is part of a number's identity (PLAN.md item 10, Path
            // A): (eq 3 3.0) is () because these are different values in the
            // model, even though (= 3 3.0) is t (same magnitude). See `=` in
            // arithmetic.rs for the magnitude-only comparison.
            // Exactness — chastyna identychnosti chysla (PLAN.md, punkt 10,
            // shliakh A): (eq 3 3.0) daie (), bo tse rizni znachennia v modeli,
            // khocha (= 3 3.0) daie t (ta sama velychyna). Dyv. `=` v
            // arithmetic.rs dlia porivniannia lyshe za velychynoiu.
            (Value::Number(left, left_exactness), Value::Number(right, right_exactness)) => {
                left == right && left_exactness == right_exactness
            }
            (Value::Rational(left), Value::Rational(right)) => left == right,
            (Value::String(left), Value::String(right)) => left == right,
            (Value::Symbol(left), Value::Symbol(right)) => left == right,
            (Value::Pair(left_head, left_tail), Value::Pair(right_head, right_tail)) => {
                left_head == right_head && left_tail == right_tail
            }
            // Vectors compare structurally, element by element — same rule
            // as Pair chains. Identity would make `(eq (vector 1) (vector 1))`
            // false while `(eq '(1) '(1))` is also false for Pairs... but the
            // docstring positions vectors as *values* for numeric workloads,
            // so structural equality is the consistent choice.
            (Value::Vector(left), Value::Vector(right)) => {
                let left = left.borrow();
                let right = right.borrow();
                left.len() == right.len() && left.iter().zip(right.iter()).all(|(l, r)| l == r)
            }
            (Value::NumericBuffer(left), Value::NumericBuffer(right)) => left == right,
            // Semantic references compare by language-owned numeric identity,
            // never by an implementation allocation or diagnostic spelling.
            (Value::SemanticRef(left), Value::SemanticRef(right)) => left == right,
            (
                Value::HostHandle {
                    kind: left_kind,
                    token: left_token,
                },
                Value::HostHandle {
                    kind: right_kind,
                    token: right_token,
                },
            ) => left_kind == right_kind && left_token == right_token,
            // Functions have identity: two separately created closures are not equal.
            // Funktsii maiut identychnist: dva okremo stvoreni zamykannia ne ye rivnymy.
            // Funktionen besitzen Identität: Zwei getrennt erzeugte Closures sind nicht gleich.
            (Value::Closure(left), Value::Closure(right)) => Rc::ptr_eq(left, right),
            (Value::Macro(left), Value::Macro(right)) => Rc::ptr_eq(left, right),
            // Same identity rule as Closure/Macro — a resource handle is
            // itself, not a value with structural equality.
            // Te same pravylo identychnosti, shcho y Closure/Macro — handle
            // resursu — tse vin sam, ne znachennia zi strukturnoiu rivnistiu.
            (Value::TcpConnection(left), Value::TcpConnection(right)) => Rc::ptr_eq(left, right),
            (Value::TcpListener(left), Value::TcpListener(right)) => Rc::ptr_eq(left, right),
            _ => false,
        }
    }
}

impl Value {
    /// Creates an embedding-owned opaque handle. Only a host integration can
    /// construct it; the reader deliberately has no corresponding syntax.
    pub fn host_handle(kind: impl Into<Rc<str>>, token: u64) -> Self {
        Self::HostHandle {
            kind: kind.into(),
            token,
        }
    }

    /// Returns the embedding-owned identity of an opaque handle.
    pub fn as_host_handle(&self) -> Option<(&str, u64)> {
        match self {
            Self::HostHandle { kind, token } => Some((kind, *token)),
            _ => None,
        }
    }

    /// Builds one host-provided callable value without adding a new evaluator
    /// form.  The host chooses only the mechanism behind a binding; Lisp still
    /// decides whether and when to call the value through ordinary evaluation.
    ///
    /// The diagnostic name is intentionally generic.  The environment binding
    /// owns the user-visible surface spelling, whose authority stays with the
    /// embedding contract rather than with this core representation.
    pub fn host_function(function: BuiltinFunction) -> Self {
        Self::Builtin(std::rc::Rc::new(Builtin {
            name: "host-capability",
            func: function,
        }))
    }

    pub fn vector(values: impl IntoIterator<Item = Value>) -> Self {
        Self::Vector(std::rc::Rc::new(std::cell::RefCell::new(
            values.into_iter().collect(),
        )))
    }

    pub fn list(values: impl IntoIterator<Item = Value>) -> Self {
        values
            .into_iter()
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .fold(Value::Nil, |tail, head| {
                Value::Pair(Rc::new(head), Rc::new(tail))
            })
    }

    pub fn is_atom(&self) -> bool {
        !matches!(self, Value::Pair(_, _))
    }

    pub fn is_truthy(&self) -> bool {
        !matches!(self, Value::Nil | Value::Bool(false))
    }

    /// Classic-Lisp truth value for a core-language predicate result:
    /// the symbol `t` (bound to itself, self-evaluating -- see
    /// `Environment::root`) for true, `Nil` for false. `eq`/`atom` use
    /// this instead of `Value::Bool` -- Boolean-ness stays a logic
    /// convention on top of the existing core types, not a separate
    /// core runtime datatype. `Value::Bool` itself is unchanged and
    /// still used by boundary code (JSON, swarm protocol, host API)
    /// that this narrow slice deliberately does not touch.
    pub fn truth(holds: bool) -> Value {
        if holds {
            Value::Symbol(Rc::from("t"))
        } else {
            Value::Nil
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", render(self, true))
    }
}

impl Value {
    /// The `princ`/`display` half of the classic Lisp print-function pair
    /// (Common Lisp `princ`, Scheme `display`): human-facing output, no
    /// quotes or escapes around strings — as opposed to `Display`/`to_string`
    /// above, which is the `prin1`/`write` half (re-readable by `read`,
    /// strings quoted and escaped). Neither replaces the other; `print`
    /// (this crate's primitive, backed by `Display`) needs to round-trip
    /// through `read`, so it keeps quoting — `princ` exists for output
    /// that's meant to be read by a person or reassembled as raw text
    /// (e.g. a tool that emits new .my source), never re-parsed as data.
    /// «princ»/«display»-polovyna klasychnoi Lisp-pary funktsii druku
    /// (Common Lisp `princ`, Scheme `display`): vyvid dlia liudyny, bez
    /// lapok i ekranuvannia navkolo riadkiv — na vidminu vid `Display`/
    /// `to_string` vyshche, shcho ye «prin1»/«write»-polovynoiu (chytaietsia nazad
    /// cherez `read`, riadky v lapkakh i ekranovani). Zhodna ne zaminiuie inshu;
    /// `print` (prymityv tsoho kreita, na osnovi `Display`) maie korektno
    /// chytatys nazad cherez `read`, tozh zberihaie lapky — `princ` isnuie dlia
    /// vyvodu, pryznachenoho liudyni chy povtornomu skladanniu yak syryi tekst
    /// (napr. instrument, shcho vydaie novyi `.my`-syrtsevyi kod), nikoly ne
    /// dlia povtornoho parsynhu yak danykh.
    pub fn to_princ_string(&self) -> String {
        render(self, false)
    }
}

/// Shared by `Display` (`quote_strings: true`, escaped — `prin1`/`write`
/// semantics) and `Value::to_princ_string` (`quote_strings: false`, raw —
/// `princ`/`display` semantics). One recursive walk, one flag, so the two
/// output modes can never silently diverge on anything but string handling.
/// Spilne dlia `Display` (`quote_strings: true`, z ekranuvanniam —
/// semantyka `prin1`/`write`) i `Value::to_princ_string` (`quote_strings:
/// false`, syryi vyvid — semantyka `princ`/`display`). Odyn rekursyvnyi
/// obkhid, odyn praporets, tozh dva rezhymy vyvodu ne mozhut movchky roziitys
/// u chomus, krim obrobky riadkiv.
fn render(value: &Value, quote_strings: bool) -> String {
    match value {
        Value::SemanticRef(semantic_id) => format!("#<semantic {semantic_id}>"),
        Value::Builtin(builtin) => format!("#<builtin {}>", builtin.name),
        Value::HostHandle { kind, .. } => format!("#<host-handle {kind}>"),
        Value::Vector(v) => {
            let items: Vec<String> = v
                .borrow()
                .iter()
                .map(|x| render(x, quote_strings))
                .collect();
            format!("#({})", items.join(" "))
        }
        Value::NumericBuffer(NumericBuffer::I32(values)) => {
            let items = values.iter().map(i32::to_string).collect::<Vec<_>>();
            format!("#i32({})", items.join(" "))
        }
        Value::NumericBuffer(NumericBuffer::F32(values)) => {
            let items = values
                .iter()
                .map(|number| {
                    if number.fract() == 0.0 {
                        format!("{number:.1}")
                    } else {
                        number.to_string()
                    }
                })
                .collect::<Vec<_>>();
            format!("#f32({})", items.join(" "))
        }
        Value::Nil => "()".to_string(),
        Value::Bool(true) => "t".to_string(),
        Value::Bool(false) => "()".to_string(),
        Value::Number(number, Exactness::Exact) => number.to_string(),
        // Rust's `{}` for f64 prints a whole number like 3.0 as "3", which
        // would silently erase the written-with-a-decimal-point intent this
        // whole redesign exists to preserve — force at least one decimal
        // digit so an inexact number always prints as inexact.
        // Rust's `{}` dlia f64 drukuie tsile chyslo na kshtalt 3.0 yak "3", shcho
        // movchky sterlo b same toi namir "napysano z krapkoiu", zarady
        // yakoho isnuie ves tsei redyzain — prymusovo drukuvaty shchonaimenshe
        // odnu desiatkovu tsyfru, shchob netochne chyslo zavzhdy drukuvalos yak
        // netochne.
        Value::Number(number, Exactness::Inexact) => {
            if number.fract() == 0.0 && number.is_finite() {
                format!("{number:.1}")
            } else {
                number.to_string()
            }
        }
        Value::Rational(number) => number.to_string(),
        Value::String(text) => {
            if quote_strings {
                let mut escaped = String::with_capacity(text.len() + 2);
                escaped.push('"');
                for ch in text.chars() {
                    match ch {
                        '"' => escaped.push_str("\\\""),
                        '\\' => escaped.push_str("\\\\"),
                        '\n' => escaped.push_str("\\n"),
                        '\t' => escaped.push_str("\\t"),
                        other => escaped.push(other),
                    }
                }
                escaped.push('"');
                escaped
            } else {
                text.to_string()
            }
        }
        Value::Symbol(symbol) => symbol.to_string(),
        Value::Pair(_, _) => render_pair(value, quote_strings),
        Value::Closure(_) => "<lambda>".to_string(),
        Value::Macro(_) => "<macro>".to_string(),
        Value::TcpConnection(_) => "<tcp-connection>".to_string(),
        Value::TcpListener(_) => "<tcp-listener>".to_string(),
    }
}

fn render_pair(value: &Value, quote_strings: bool) -> String {
    let mut out = String::from("(");
    let mut current = value;
    let mut first = true;
    loop {
        match current {
            Value::Pair(head, tail) => {
                if !first {
                    out.push(' ');
                }
                out.push_str(&render(head, quote_strings));
                current = tail;
                first = false;
            }
            Value::Nil => {
                out.push(')');
                return out;
            }
            tail => {
                out.push_str(" . ");
                out.push_str(&render(tail, quote_strings));
                out.push(')');
                return out;
            }
        }
    }
}

impl Drop for Value {
    fn drop(&mut self) {
        if !matches!(self, Value::Pair(_, _)) {
            return;
        }

        let mut worklist = Vec::new();
        worklist.push(std::mem::replace(self, Value::Nil));

        while let Some(value) = worklist.pop() {
            let mut value = std::mem::ManuallyDrop::new(value);
            match &mut *value {
                Value::Pair(head, tail) => {
                    let head = unsafe { std::ptr::read(head) };
                    let tail = unsafe { std::ptr::read(tail) };
                    if let Ok(inner) = Rc::try_unwrap(head) {
                        if matches!(inner, Value::Pair(_, _)) {
                            worklist.push(inner);
                        }
                    }
                    if let Ok(inner) = Rc::try_unwrap(tail) {
                        if matches!(inner, Value::Pair(_, _)) {
                            worklist.push(inner);
                        }
                    }
                }
                _ => {
                    unsafe { std::mem::ManuallyDrop::drop(&mut value) };
                }
            }
        }
    }
}

#[cfg(test)]
mod host_handle_tests {
    use super::Value;

    #[test]
    fn host_handle_hides_its_token_when_rendered() {
        let handle = Value::host_handle("cyberpunk.IScriptable", 0x1234_5678);
        assert_eq!(
            handle.as_host_handle(),
            Some(("cyberpunk.IScriptable", 0x1234_5678))
        );
        assert_eq!(handle.to_string(), "#<host-handle cyberpunk.IScriptable>");
        assert_ne!(handle.to_string(), "#<host-handle 305419896>");
    }
}
