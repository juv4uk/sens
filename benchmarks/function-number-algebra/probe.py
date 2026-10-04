#!/usr/bin/env python3
import json
from collections import Counter

CURRENT = {
    3: {
        0b000:"EMPTY",0b001:"QUOTE",0b010:"ATOM",0b011:"CDR",
        0b100:"CAR",0b101:"EQ",0b110:"COND",0b111:"CONS",
    },
    4: {
        0b0000:"APPLY",0b0001:"EVAL",0b0010:"LAMBDA",0b0011:"DEFINE",
        0b0100:"NOT",0b0101:"NULL",0b0110:"CDAR",0b0111:"CDDR",
        0b1000:"CAAR",0b1001:"CADR",0b1010:"LOOKUP",0b1011:"BIND",
        0b1100:"EVCON",0b1101:"EVLIS",0b1110:"LIST",0b1111:"APPEND",
    },
    5: {
        0b00000:"EVALQUOTE",0b00001:"FUNCTION",0b00010:"FEXPR",0b00011:"MACRO",
        0b00100:"LABEL",0b00101:"PROG",0b00110:"SET",0b00111:"SETQ",
        0b01000:"ZEROP",0b01001:"NUMBERP",0b01010:"PLUS",0b01011:"DIFFERENCE",
        0b01100:"CDAAR",0b01101:"CDADR",0b01110:"CDDAR",0b01111:"CDDDR",
        0b10000:"CAAAR",0b10001:"CAADR",0b10010:"CADAR",0b10011:"CADDR",
        0b10100:"REVERSE",0b10101:"REVERSE-ONTO",0b10110:"TIMES",0b10111:"QUOTIENT",
        0b11000:"GO",0b11001:"RETURN",0b11010:"LESSP",0b11011:"GREATERP",
        0b11100:"ASSOC",0b11101:"MEMBER",0b11110:"PAIRLIS",0b11111:"SUBST",
    }
}

def bits(x,w):
    return format(x,f"0{w}b")

def full_add_stats(w):
    vals=range(1<<w)
    out=Counter(a+b for a in vals for b in vals)
    ow=w+1
    return {
        "input_width":w,
        "output_width":ow,
        "ordered_pairs":(1<<w)**2,
        "unique_outputs":len(out),
        "coverage":f"{len(out)}/{1<<ow}",
        "missing_outputs":[bits(x,ow) for x in range(1<<ow) if x not in out],
        "max_output":bits(max(out),ow),
    }

def full_mul_stats(w):
    vals=range(1<<w)
    out={a*b for a in vals for b in vals}
    ow=2*w
    squares=[a*a for a in vals]
    return {
        "input_width":w,
        "output_width":ow,
        "ordered_pairs":(1<<w)**2,
        "unique_products":len(out),
        "product_coverage":f"{len(out)}/{1<<ow}",
        "square_outputs":[bits(x,ow) for x in squares],
        "square_count":len(squares),
    }

def concat_stats(w):
    vals=range(1<<w)
    out={(a<<w)|b for a in vals for b in vals}
    ow=2*w
    return {
        "input_width":w,
        "output_width":ow,
        "ordered_pairs":(1<<w)**2,
        "unique_outputs":len(out),
        "coverage":f"{len(out)}/{1<<ow}",
        "bijective":len(out)==(1<<ow),
    }

def append_stats(w):
    vals=range(1<<w)
    out0={(x<<1) for x in vals}
    out1={(x<<1)|1 for x in vals}
    union=out0|out1
    return {
        "input_width":w,
        "output_width":w+1,
        "input_count":1<<w,
        "outputs_with_both_bits":len(union),
        "coverage":f"{len(union)}/{1<<(w+1)}",
        "bijective_pair_encoding":len(union)==(1<<(w+1)),
    }

def xor_stats(w):
    vals=range(1<<w)
    out=Counter(a^b for a in vals for b in vals)
    counts=set(out.values())
    return {
        "width":w,
        "ordered_pairs":(1<<w)**2,
        "unique_outputs":len(out),
        "closure":len(out)==(1<<w),
        "uniform_preimages":sorted(counts),
    }

def square_predictions(w):
    ow=2*w
    result=[]
    for x,name in CURRENT[w].items():
        result.append({
            "input_bits":bits(x,w),
            "input_projection":name,
            "output_width":ow,
            "square_bits":bits(x*x,ow),
        })
    return result

report={
    "issue":"#3359",
    "principle":"exact-width binary resident -> direct math -> exact-width binary result",
    "width_laws":{
        "bitwise":"Wn x Wn -> Wn",
        "append":"Wn x bit -> W(n+1)",
        "full_add":"Wn x Wn -> W(n+1)",
        "full_mul":"Wn x Wn -> W(2n)",
        "concat":"Wa x Wb -> W(a+b)",
    },
    "same_width_xor":[xor_stats(w) for w in (3,4,5)],
    "append":[append_stats(w) for w in (3,4)],
    "full_add":[full_add_stats(w) for w in (3,4)],
    "concat_products":[concat_stats(w) for w in (3,4)],
    "full_multiply":[full_mul_stats(w) for w in (3,4)],
    "square_predictions":{
        "D3_to_W6":square_predictions(3),
        "D4_to_W8":square_predictions(4),
    },
    "observations":[
        "XOR is closed on every exact-width space and every result has uniform preimage count.",
        "append-bit maps W3×Bit bijectively to W4 and W4×Bit bijectively to W5.",
        "full unsigned ADD maps W3×W3 to 15/16 W4 numbers and W4×W4 to 31/32 W5 numbers; only all-ones is unreachable.",
        "concat maps W3×W3 bijectively onto all W6 numbers and W4×W4 bijectively onto all W8 numbers.",
        "full MUL maps W3×W3 into W6 with 26/64 distinct products; W4×W4 into W8 with 90/256 distinct products.",
        "square is now width-correct: W3 square outputs W6; W4 square outputs W8."
    ],
}

assert report["append"][0]["coverage"]=="16/16"
assert report["append"][1]["coverage"]=="32/32"
assert report["full_add"][0]["coverage"]=="15/16"
assert report["full_add"][0]["missing_outputs"]==["1111"]
assert report["full_add"][1]["coverage"]=="31/32"
assert report["full_add"][1]["missing_outputs"]==["11111"]
assert report["concat_products"][0]["coverage"]=="64/64"
assert report["concat_products"][1]["coverage"]=="256/256"
assert report["full_multiply"][0]["product_coverage"]=="26/64"
assert report["full_multiply"][1]["product_coverage"]=="90/256"
assert all(x["closure"] for x in report["same_width_xor"])

print(json.dumps(report,indent=2,sort_keys=True))
