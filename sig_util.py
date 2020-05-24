def signals_hold(sig):
    for s in sig:
        s.append(s[-1])

def signals_wl_enable(sig, idx):
    if type(idx) is not int:
        raise ValueError()
    for i, s in enumerate(sig):
        if i == idx:
            s.append(1)
        else:
            s.append(0)

def signals_wl_disable(sig):
    for s in sig:
        s.append(0)

def signals_bl_set(bl, blb, val):
    for b, v in zip(bl, val):
        b.append(v)
    for b, v in zip(blb, val):
        b.append(1-v)

def signals_to_str(sigs_all, idx):
    s = ""
    for sigs in sigs_all:
        sig = [x[idx] for x in reversed(sigs)]
        s += "".join([str(x) for x in sig])
    return s

