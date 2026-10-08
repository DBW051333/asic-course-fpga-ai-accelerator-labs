open_project /home/ding/vivado_project/Lab4_tree4_1221_clk4p8/Lab4.xpr
set_property xsim.simulate.runtime {12000ns} [get_filesets sim_1]
launch_simulation -mode behavioral
close_sim
close_project
