// Portable FPGA-ready D1/D2/D3 subset: actual T5 bytes enter as 8-bit input.
// Independent hardware transport and bounded evaluator, no host-Lisp tags.
module sens_silicon_d3 (
    input wire clk,
    input wire rst,
    input wire byte_valid,
    output wire byte_ready,
    input wire [7:0] byte_data,
    input wire byte_last,
    output wire done,
    output wire valid,
    output wire error,
    output wire result_is_predicate,
    output wire result_bit
);
    wire word_valid;
    wire [3:0] width;
    wire [8:0] bits;
    wire transport_done;
    wire transport_error;
    sens_t5_decoder transport (
        .clk(clk), .rst(rst), .in_valid(byte_valid), .in_ready(byte_ready),
        .in_byte(byte_data), .in_last(byte_last), .word_valid(word_valid),
        .word_width(width), .word_bits(bits), .done(transport_done),
        .error(transport_error)
    );
    sens_d3_microcore evaluator (
        .clk(clk), .rst(rst), .word_valid(word_valid),
        .word_width(width), .word_bits(bits),
        .input_done(transport_done), .input_error(transport_error),
        .done(done), .valid(valid), .error(error),
        .result_predicate(result_is_predicate), .result_bit(result_bit)
    );
endmodule
