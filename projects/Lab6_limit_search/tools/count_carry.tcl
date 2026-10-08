set_param general.maxThreads 4
open_checkpoint /home/ding/vivado_project/Lab6_limit_search/dual512_lookup/results/synth.dcp
set groups [dict create]
foreach cell [get_cells -hier -filter {REF_NAME == CARRY4}] {
 set n [get_property NAME $cell]
 if {[regexp {network/u_fc1/mult\[[0-9]+\]\.half\[[0-9]+\]\.([^/]+)} $n -> node]} {
  regsub {(_reg|\[[0-9]+\]|_i_[0-9]+|__.*).*} $node {} node
  set key "fc1_mult/$node"
 } elseif {[regexp {network/u_fc1/(tree[01])} $n -> node]} {set key $node
 } else {set key other}
 dict incr groups $key
}
set f [open /home/ding/vivado_project/Lab6_limit_search/results/carry_breakdown.txt w]
dict for {key value} $groups {puts $f "$key $value"}
close $f
exit
