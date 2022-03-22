//custom_verilog.v
module foo(
    input [15:0] i0,
    input [15:0] i1,
    output [15:0] o
);
    assign o = i0 + i1;

endmodule