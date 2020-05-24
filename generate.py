import numpy as np
from random import randint
from sig_util import signals_hold, signals_wl_enable, signals_wl_disable, signals_bl_set, signals_to_str

MSB_BIT, LSB_BIT = 0, 1
def random_events(n_event=20):
    events = [('init',)]
    for t in range(n_event):
        idx_event = randint(0,2)
        event_name = event_all[idx_event]

        if event_name == 'sram-msb-write' or event_name == 'sram-lsb-write':
            idx_mac = randint(0, nmac-1)
            val_mac = randint(0,1)
            events.append((event_name, idx_mac, val_mac))

        elif event_name == 'vin':
            val = [randint(0,1) for i in range(nmac)]
            events.append((event_name, val))
    return events

# Convert operation sequence into signal time step
def events_to_signals(events, nmac=4, ncol=1):
    # Variable definition
    bl = [[] for _ in range(ncol)]
    blb = [[] for _ in range(ncol)]
    wlmsb = [[] for _ in range(nmac)]
    wllsb = [[] for _ in range(nmac)]
    vips = [[] for _ in range(nmac)]
    vims = [[] for _ in range(nmac)]
    
    for evt in events:
        event_type = evt[0]
    
        # Initialize circuit
        if event_type == 'init':
            # Write 0 to each SRAM initially
            signals_bl_set(bl, blb, [0] * ncol)
            for i in range(nmac):
                wlmsb[i].append(1)
                wllsb[i].append(1)

            # CLR operation
            for i in range(nmac):
                vips[i].append(0)
                vims[i].append(0)
    
        elif event_type == 'sram-lsb-write':
            sram_index = evt[1]
            sram_value = evt[2]
            if len(sram_value) != ncol:
                raise ValueError()

            # Write val into the SRAM
            signals_bl_set(bl, blb, sram_value)
            signals_wl_enable(wllsb, sram_index)
            signals_wl_disable(wlmsb)

            signals_hold(vips)
            signals_hold(vims)
    
        elif event_type == 'sram-msb-write':
            sram_index = evt[1]
            sram_value = evt[2]
            if len(sram_value) != ncol:
                raise ValueError()
            signals_bl_set(bl, blb, sram_value)
            signals_wl_enable(wlmsb, sram_index)
            signals_wl_disable(wllsb)
            signals_hold(vips)
            signals_hold(vims)
    
        elif event_type == 'vin':
            vin_value = evt[1]
            if len(vin_value) != nmac:
                vin_len = len(vin_value)
                errmsg = "vin (len %d) should be length %d" % (vin_len, nmac)
                raise ValueError(errmsg)

            signals_wl_disable(wllsb)
            signals_wl_disable(wlmsb)
            signals_bl_set(bl, blb, [0] * ncol) # Don't care
            for v, vip, vim in zip(vin_value, vips, vims):
                vip.append(v)
                vim.append(1-v)
        else:
            raise ValueError()

    signals = {'bl': bl, 'blb': blb, 'wlmsb': wlmsb, 'wllsb': wllsb, 'vips': vips, 'vims': vims}

    return signals

# Get the SRAM state from a signal sequence
def signals_to_status(bl_all, blb_all, wlmsb_all, wllsb_all, nmac=16, ncol=4):
    sram = []
    for i in range(nmac):
        sram_l1 = []
        for j in range(ncol):
            sram_l2 = [[] for _ in range(2)]
            sram_l1.append(sram_l2)
        sram.append(sram_l1)

    if len(bl_all[0]) != len(wlmsb_all[0]):
        raise ValueError()

    for t in range(len(bl_all[0])):
        bl  = [b[t] for b in bl_all]
        blb = [b[t] for b in blb_all]
        wlmsb = [x[t] for x in wlmsb_all]
        wllsb = [x[t] for x in wllsb_all]

        for i, w in enumerate(wlmsb):
            for j, b in enumerate(bl):
                new_value = b if w == 1 else sram[i][j][MSB_BIT][-1]
                sram[i][j][MSB_BIT].append(new_value)
        
        for i, w in enumerate(wllsb):
            for j, b in enumerate(bl):
                new_value = b if w == 1 else sram[i][j][LSB_BIT][-1]
                sram[i][j][LSB_BIT].append(new_value)

    return sram

# Export signal time step into digital vector file
def export_signals(signals, output_tb_fname, nmac, ncol, events, vdd=0.8):

    # Print variable name
    vname_str = "vname " + "wlmsb_w<[%d:0]> " % (nmac-1) + "wllsb_w<[%d:0]> " % (nmac-1) + "bl<[%d:0]> " % (ncol-1) + "blb<[%d:0]> " % (ncol-1) + "vip_w<[%d:0]> " % (nmac-1) + "vim_w<[%d:0]> " % (nmac-1)
    print(vname_str)
    
    # Write header (radix, io, vname) to output .vec
    fin = open(output_tb_fname, 'w')
    fin.write("radix " + " ".join(["1"] * (4 * nmac + 2 * ncol)) + '\n')
    fin.write("io " + " ".join(["i"] * (4 * nmac + 2 * ncol)) + '\n')
    fin.write(vname_str + '\n')
    
    # Write config (tunit, trise, tfall, vih, vil) to output .vec
    fin.write("tunit ns\ntrise 0.02\ntfall 0.02\nvih %.1f\nvil 0.0\n\n" % vdd)
    
    # Write signal value in each time slot
    bl, blb = signals['bl'], signals['blb']
    vips, vims = signals['vips'], signals['vims']
    wlmsb, wllsb = signals['wlmsb'], signals['wllsb']
    t_total = len(vips[0])

    for idx in range(t_total):
        evt_name = "/".join([str(x) for x in events[idx]])
        comment = evt_name
    
        # Array value should be written from MSB to LSB
        value_str = signals_to_str([wlmsb, wllsb, bl, blb, vips, vims], idx=idx)
        fin.write("%d " % idx + value_str + " ; " + comment + '\n')

if __name__ == "__main__":
    # nmac = 4
    vdd = 0.8
    output_tb_fname = "input.vec"
    event_all = ['sram-msb-write', 'sram-lsb-write', 'vin']

    events = random_events()
    signals, status = events_to_signals(events)
    export_signals(signals)



    vop_ideal, vom_ideal = get_ideal_voltage(signals, status)
    
    # Write out vop_ideal values
    t_total = len(vop_ideal)
    fvop = open('vop_ideal.out', 'w')
    for idx in range(t_total):
        if idx > 0:
            fvop.write("%e %e\n" % ((idx-0.001) * 1e-9, vop_ideal[idx-1]))
        fvop.write("%e %e\n" % (idx * 1e-9, vop_ideal[idx]))
    
    # Write out vom_ideal values
    fvom = open('vom_ideal.out', 'w')
    for idx in range(t_total):
        if idx > 0:
            fvom.write("%e %e\n" % ((idx-0.001) * 1e-9, vom_ideal[idx-1]))
        fvom.write("%e %e\n" % (idx * 1e-9, vom_ideal[idx]))
