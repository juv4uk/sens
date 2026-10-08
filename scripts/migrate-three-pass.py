            target.tok,
        )
    name_tok = target.items[0].tok
    params = ListNode(target.items[1:], None, target.tok)
    lambda_names = lambda_parameter_names(params)
    words = [D2_OPEN, "0011", D2_SEP]
    words.extend(encode_text7_identifier(name_tok.text, text7, name_tok))
    words.append(D2_SEP)
    words.extend((D2_OPEN, "0010", D2_SEP))
    words.extend(encode_lambda_params(params, text7))
    words.append(D2_SEP)
    words.extend(
        encode(
            body,
            resolver,
            text7,
            quoted=False,
            lexical_env=tuple(lambda_names) + tuple(lexical_env),
        )
    )
    words.extend((D2_CLOSE, D2_CLOSE))
    return words


def encode_string(node: String,text7):
    return [node.tok.text]


def encode_clause(node,resolver,text7,lexical_env=()):
    """COND clause is structural; nested executable expressions retain scope."""
    if not isinstance(node,ListNode):
        return encode(node,resolver,text7,quoted=False,lexical_env=lexical_env)
    if not node.items and node.tail is None:
        return [D3_EMPTY]
    words=[D2_OPEN]
    for idx,item in enumerate(node.items):
        if idx:
            words.append(D2_SEP)
        if isinstance(item,ListNode):
            words.extend(
                encode(item,resolver,text7,quoted=False,lexical_env=lexical_env)
            )
        else:
            words.extend(
                encode(item,resolver,text7,quoted=True,lexical_env=())
            )
    if node.tail is not None:
        words.append(D2_DOT)
        words.extend(encode(node.tail,resolver,text7,quoted=True,lexical_env=()))
    words.append(D2_CLOSE)
    return words


def encode_let_bindings(bindings,resolver,text7,lexical_env=(),sequential=False):
    if bindings.tail is not None:
        raise MigrationError(
            "LET binding list must be a proper list",
            bindings.tok,
        )
    words=[D2_OPEN]
    bound=list(lexical_env)
    for index,binding in enumerate(bindings.items):
        if index:
            words.append(D2_SEP)
        if not isinstance(binding,ListNode) or binding.tail is not None:
            raise MigrationError(
                "LET binding must be a proper (name value) list",
                binding.tok if isinstance(binding,ListNode) else None,
            )
        if not binding.items or len(binding.items)>2:
            raise MigrationError(
                "LET binding must contain a name and at most one initializer",
                binding.tok,
            )
        name=binding.items[0]
        if not isinstance(name,Atom):
            raise MigrationError(
                "LET binding name must be an identifier atom",
                name.tok if isinstance(name,Atom) else binding.tok,
            )
        init_env=tuple(bound) if sequential else lexical_env
        words.extend(encode_text7_identifier(name.tok.text,text7,name.tok))
        words.append(D2_SEP)
        if len(binding.items)==2:
            words.extend(
                encode(
                    binding.items[1],
                    resolver,
                    text7,
                    quoted=False,
                    lexical_env=init_env,
                )
            )
        else:
            words.extend([D3_EMPTY])
        if name.tok.text not in bound:
            bound.append(name.tok.text)
    words.append(D2_CLOSE)
    return words,tuple(bound)


def encode(node,resolver,text7,quoted=False,lexical_env=()):
    if isinstance(node,ListNode):
        if not node.items and node.tail is None:
            return [D3_EMPTY]

        if not quoted:
            shorthand = encode_define_shorthand(node,resolver,text7,lexical_env)
            if shorthand is not None:
                return shorthand

        words=[D2_OPEN]
        head_bits=None
        lambda_names=()

        for idx,item in enumerate(node.items):
            if idx:
                words.append(D2_SEP)

            if idx==0 and not quoted and isinstance(item,Atom):
                # Lexical source bindings take precedence over global/current
                # callable surfaces. This is the scalable shadow-safe rule:
                # source scope, not spelling alone, decides the head.
                if item.tok.text in lexical_env:
                    words.extend(encode_text7_identifier(
                        item.tok.text,text7,item.tok
                    ))
                    continue
                head,_=resolver.head(item.tok)
                head_bits=head[0]
                words.extend(head)
                continue

            # Explicit QUOTE: everything below is data, with no live lexical scope.
            if not quoted and head_bits=="001":
                words.extend(
                    encode(item,resolver,text7,quoted=True,lexical_env=())
                )
                continue

            # D6 LET / LET*: binding lists are structural D2 containers;
            # only binder names and lexical references receive contextual Text7.
            # Parallel LET initializers see the outer scope. LET* initializers
            # additionally see bindings introduced earlier in the same list.
            if not quoted and head_bits in ("001000","001001") and idx==1:
                if not isinstance(item,ListNode):
                    raise MigrationError(
                        "LET binding list must be a proper list",
                        item.tok if isinstance(item,Atom) else None,
                    )
                let_sequential=head_bits=="001001"
                binding_words,let_names=encode_let_bindings(
                    item,
                    resolver,
                    text7,
                    lexical_env=lexical_env,
                    sequential=let_sequential,
                )
                words.extend(binding_words)
                lambda_names=let_names
                continue

            if not quoted and head_bits in ("001000","001001") and idx>=2:
                words.extend(
                    encode(
                        item,
                        resolver,
                        text7,
                        quoted=False,
                        lexical_env=lambda_names,
                    )
                )
                continue

            # D4 LAMBDA: parameter declarations are one contextual Text7 frame
            # per identifier; its body executes under the newly introduced scope.
            if not quoted and head_bits=="0010" and idx==1:
                if not isinstance(item,ListNode):
                    raise MigrationError(
                        "lambda parameters must be a proper list",
                        item.tok if isinstance(item,Atom) else None,
                    )
                lambda_names=lambda_parameter_names(item)
                words.extend(encode_lambda_params(item,text7))
                continue

            if not quoted and head_bits=="0010" and idx>=2:
                body_env=tuple(lambda_names)+tuple(lexical_env)
                words.extend(
                    encode(
                        item,
                        resolver,
                        text7,
                        quoted=False,
                        lexical_env=body_env,
                    )
                )
                continue

            # D4 DEFINE: the binding target gets the same contextual Text7 frame
            # used by global call heads. Shorthand signature remains data-shaped.
            if not quoted and head_bits=="0011" and idx==1:
                if isinstance(item,Atom):
                    words.extend(
                        encode_text7_identifier(item.tok.text,text7,item.tok)
                    )
                    continue
                if isinstance(item,ListNode):
                    words.extend(
                        encode(item,resolver,text7,quoted=True,lexical_env=())
                    )
                    continue

            # COND clauses are structural containers, not call heads.
            if not quoted and head_bits=="110":
                words.extend(
                    encode_clause(
                        item,
                        resolver,
                        text7,
                        lexical_env=lexical_env,
                    )
                )
                continue

            words.extend(
                encode(
                    item,
                    resolver,
                    text7,
                    quoted=quoted,
                    lexical_env=lexical_env,
                )
            )

        if node.tail is not None:
            words.append(D2_DOT)
            words.extend(
                encode(node.tail,resolver,text7,quoted=True,lexical_env=())
            )
        words.append(D2_CLOSE)
        return words

    if isinstance(node,Quote):
        return [
            D2_OPEN,
            "001",
            D2_SEP,
            *encode(node.value,resolver,text7,quoted=True,lexical_env=()),
            D2_CLOSE,
        ]
    if isinstance(node,String):
        return encode_string(node,text7)