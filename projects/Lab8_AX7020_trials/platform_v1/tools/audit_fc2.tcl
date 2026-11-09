set fc2_ffs [get_cells -hier -filter {NAME =~ *u_fc2* && (REF_NAME == FDRE || REF_NAME == FDSE || REF_NAME == FDCE || REF_NAME == FDPE)}]
set old_acc [get_cells -hier -filter {NAME =~ *u_fc2* && (NAME =~ *even_acc* || NAME =~ *odd_acc* || NAME =~ *merge_low* || NAME =~ *merge_a* || NAME =~ *merge_b* || NAME =~ *parity_local*)}]
if {[llength $old_acc]} {error "Old split accumulation unexpectedly retained"}
set acc [get_cells -hier -filter {NAME =~ *u_fc2*acc_reg* && (REF_NAME == FDRE || REF_NAME == FDSE || REF_NAME == FDCE || REF_NAME == FDPE)}]
set snapshot [get_cells -hier -filter {NAME =~ *u_fc2*snapshot_reg* && (REF_NAME == FDRE || REF_NAME == FDSE || REF_NAME == FDCE || REF_NAME == FDPE)}]
if {![llength $acc] || ![llength $snapshot]} {error "Accumulator or required snapshot missing"}
set f [open $root/results/fc2_register_audit.json w]
puts $f "{\"pass\":true,\"fc2_ff\":[llength $fc2_ffs],\"accumulator_ff\":[llength $acc],\"snapshot_ff\":[llength $snapshot],\"old_split_accumulation_cells\":0}"
close $f
