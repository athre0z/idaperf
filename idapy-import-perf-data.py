COLOR_MIN_WEIGHT  = .001
COLOR_BLEND_COEFF = 10.
COLOR_WEAK        = 0x000044
COLOR_STRONG      = 0x0000EE
CREATE_COMMENTS   = True
# perf samples tend to be on the next instruction after the
# actual slow instruction. this allows to correct for that.
INSN_OFFSET       = -1

import csv
from collections import namedtuple

Sym = namedtuple("Sym", "name addr ctr_tot ctr_top")

syminfo = []
with open(idaapi.ask_file(False, "*.csv", "Select perf csv dump"), "r") as f:
    reader = csv.reader(f)
    for _, ctr_tot, ctr_top, name in reader:
        sym, offs = name.split('+')
        addr = idaapi.get_name_ea(BADADDR, sym)
        if addr == BADADDR:
            print("Skipping unknown symbol: {}".format(sym))
            continue
        addr += int(offs, 16)
        syminfo.append(Sym(name, addr, int(ctr_tot), int(ctr_top)))

total_samples = sum(x.ctr_top for x in syminfo)

def split_color(x):
    return x & 0xFF, (x & 0xFF00) >> 8, (x & 0xFF0000) >> 16

def recombine_color(r, g, b):
    return r | (g << 8) | (b << 16)

assert recombine_color(*split_color(0xAABBCC)) == 0xAABBCC

def blend_colors(a, b, w):
    assert 0. <= w <= 1.
    return recombine_color(*(
        int(x * (1. - w) + y * w)
        for (x, y) in
        zip(split_color(a), split_color(b))
    ))

for sym in syminfo:
    weight = float(sym.ctr_top) / total_samples
    if weight < COLOR_MIN_WEIGHT:
        continue

    color_weight = min(1., COLOR_BLEND_COEFF * weight)
    color = blend_colors(COLOR_WEAK, COLOR_STRONG, color_weight)

    ea = sym.addr
    for _ in range(abs(INSN_OFFSET)):
        new_ea = (
            idaapi.next_head(ea, BADADDR)
            if INSN_OFFSET > 0 else
            idaapi.prev_head(ea, 0)
        )

        if new_ea != BADADDR:
            ea = new_ea

    idaapi.set_item_color(ea, color)
    if CREATE_COMMENTS:
        idaapi.set_cmt(ea, "{:.02%}".format(weight), False)