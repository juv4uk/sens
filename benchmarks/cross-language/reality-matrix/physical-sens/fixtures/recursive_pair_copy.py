"""Рекурсивно копіює proper pair-list з D1-подібними значеннями та NIL."""


def copy_pair(value):
    if value is None:
        return None
    head, tail = value
    return (head, copy_pair(tail))


def render_atom(value):
    if value is True:
        return "1"
    if value is False:
        return "0"
    if value is None:
        return "()"
    raise TypeError(f"unexpected atom: {value!r}")


def render_list(value):
    fields = []
    while value is not None:
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError(f"improper pair-list: {value!r}")
        head, value = value
        fields.append(render_atom(head))
    return "(" + " ".join(fields) + ")"


source = (True, (False, (None, None)))
result = copy_pair(source)
print(render_list(result))
