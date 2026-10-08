# 将课程提供的一元素一行的 8 位 COE 文件重新打包为并行 BRAM 可直接加载的 COE。
# 用法：tclsh pack_coe.tcl <输入.coe> <输出.coe> <每行元素数>
# 例：tclsh pack_coe.tcl fc2.0.weight.coe fc2_weight_32.coe 32

if {$argc != 3} {
    puts stderr "usage: tclsh pack_coe.tcl <input.coe> <output.coe> <elements_per_word>"
    exit 2
}

set in_path [lindex $argv 0]
set out_path [lindex $argv 1]
set lanes [lindex $argv 2]
if {![string is integer -strict $lanes] || $lanes <= 0} {
    puts stderr "elements_per_word must be a positive integer"
    exit 2
}

set in_file [open $in_path r]
set values {}
while {[gets $in_file line] >= 0} {
    set line [string trim $line]
    if {$line eq "" || [string match "memory_initialization_*" $line]} {
        continue
    }
    set bits [string trim $line ",;"]
    if {$bits ne ""} {
        if {![regexp {^[01]{8}$} $bits]} {
            puts stderr "invalid 8-bit binary value: $bits"
            close $in_file
            exit 2
        }
        lappend values $bits
    }
}
close $in_file

if {[llength $values] % $lanes != 0} {
    puts stderr "[llength $values] values cannot be divided into $lanes lanes"
    exit 2
}

set out_file [open $out_path w]
puts $out_file "memory_initialization_radix = 2;"
puts $out_file "memory_initialization_vector ="
set words [expr {[llength $values] / $lanes}]
for {set word 0} {$word < $words} {incr word} {
    set packed ""
    for {set lane 0} {$lane < $lanes} {incr lane} {
        append packed [lindex $values [expr {$word * $lanes + $lane}]]
    }
    puts -nonewline $out_file $packed
    if {$word == $words - 1} {
        puts $out_file ";"
    } else {
        puts $out_file ","
    }
}
close $out_file
puts "wrote $words words, [expr {$lanes * 8}] bits each: $out_path"
