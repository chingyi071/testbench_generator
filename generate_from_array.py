import numpy as np
from generate import events_to_signals, export_signals, signals_to_status

def get_operations_from_array( input_weights, input_data ):
    events = []
    events.append(('init',))
    
    for i, w in enumerate(input_weights):
        msb_value = (w > 0).astype(np.int)
        lsb_value = ((w + 1) % 4 == 0).astype(np.int)
        if (2 * msb_value + lsb_value != (w + 3) // 2).any():
            raise Exception()
        events.append(('sram-msb-write', i, msb_value.tolist()))
        events.append(('sram-lsb-write', i, lsb_value.tolist()))

    for each_input_data in input_data:
        input_level = [(x // 3) for x in each_input_data]
        events.append(('vin', input_level))

    return events

# Structure configuration
nsample = 20
nmac = 16
ncol = 4
vdd = 0.8
output_tb_fname = "input.vec"

# Input setting
input_data = (3 * np.random.randint(0, 2, (nsample, nmac))).tolist()
input_weights = (2 * np.random.randint(0, 4, (nmac, ncol)) - 3)

# Generate testbench
events = get_operations_from_array( input_weights, input_data )
signals = events_to_signals(events, nmac=nmac, ncol=ncol)
sram_new = signals_to_status(signals['bl'], signals['blb'], signals['wlmsb'], signals['wllsb'])
export_signals(signals, output_tb_fname, nmac=nmac, events=events, ncol=ncol)

# Generate groundtruth
t_init = 2 * nmac + 1
for col_idx in range(ncol):

    ideal_vop_seq = [0] * t_init
    ideal_vom_seq = [0] * t_init
    col_weights = input_weights[:,col_idx]

    # Calculate result from each time step (One input vector per time step)
    for each_input_data in input_data:
        ideal_value = 2 * sum([w * x for x, w in zip(each_input_data, col_weights)]) - 3 * sum(col_weights)
        ideal_vop = 0.4 + 0.4 * ideal_value / (3 * 3 * nmac)
        ideal_vom = 0.4 - 0.4 * ideal_value / (3 * 3 * nmac)
        ideal_vop_seq.append(ideal_vop)
        ideal_vom_seq.append(ideal_vom)

    # Export groundtruth to a file
    fvop = open("vop%d.out" % col_idx, 'w')
    for idx in range(len(ideal_vop_seq)):
        if idx > 0:
            fvop.write("%e %e\n" % ((idx-0.001) * 1e-9, ideal_vop_seq[idx-1]))
        fvop.write("%e %e\n" % (idx * 1e-9, ideal_vop_seq[idx]))
