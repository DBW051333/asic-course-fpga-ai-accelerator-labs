# Keep high-fanout CE/state data nets off the global clock network.
# The real PS FCLK clock retains its normal BUFG.
set controls [get_nets -hier -filter {NAME =~ *core_ce* || NAME =~ *FSM_onehot_state_r_reg*}]
set_property CLOCK_BUFFER_TYPE NONE $controls
