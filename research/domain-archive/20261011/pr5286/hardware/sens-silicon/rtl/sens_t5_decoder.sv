// Synthesizable bounded physical T5 byte -> exact-width D1..D9 word stream.
// Does NOT interpret domain meanings. One physical byte holds five base-3
// trits; trit 2 is an inter-word separator or final padding (0..4 trits).
// Input accepted only while ready; in_last marks the final byte.
module sens_t5_decoder (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [7:0] in_byte,
    input wire in_last,
    output reg word_valid,
    output reg [3:0] word_width,
    output reg [8:0] word_bits,
    output reg done,
    output reg error
);
    localparam [2:0] IDLE = 0, TRITS = 1, FINISH = 2,
                     FINISH_WAIT = 3, HALTED = 4;
    reg [2:0] state;
    reg [7:0] held_byte;
    reg held_last;
    reg [2:0] trit_index;
    reg [3:0] accum_width;
    reg [8:0] accum_bits;
    reg [2:0] consecutive_twos;
    reg seen_word;
    reg [1:0] trit;

    assign in_ready = (state == IDLE) && !error && !done;

    // Division by constants: synthesizers can implement a tiny fixed decoder.
    always @* begin
        case (trit_index)
            0: trit = (held_byte / 8'd81) % 3;
            1: trit = (held_byte / 8'd27) % 3;
            2: trit = (held_byte / 8'd9) % 3;
            3: trit = (held_byte / 8'd3) % 3;
            default: trit = held_byte % 3;
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            held_byte <= 0;
            held_last <= 0;
            trit_index <= 0;
            accum_width <= 0;
            accum_bits <= 0;
            consecutive_twos <= 0;
            seen_word <= 0;
            word_valid <= 0;
            word_width <= 0;
            word_bits <= 0;
            done <= 0;
            error <= 0;
        end else begin
            word_valid <= 0;
            case (state)
                IDLE: if (in_valid) begin
                    if (in_byte >= 8'd243) begin
                        error <= 1;
                        state <= HALTED;
                    end else begin
                        held_byte <= in_byte;
                        held_last <= in_last;
                        trit_index <= 0;
                        state <= TRITS;
                    end
                end
                TRITS: begin
                    if (trit == 2) begin
                        if (accum_width != 0) begin
                            word_valid <= 1;
                            word_width <= accum_width;
                            word_bits <= accum_bits;
                            seen_word <= 1;
                            accum_width <= 0;
                            accum_bits <= 0;
                            consecutive_twos <= 1;
                        end else if (consecutive_twos >= 4) begin
                            // Five successive '2' trits are neither one
                            // word separator nor canonical tail padding.
                            error <= 1;
                            state <= HALTED;
                        end else begin
                            consecutive_twos <= consecutive_twos + 1'b1;
                        end
                    end else if (consecutive_twos > 1 || accum_width >= 9) begin
                        // More than one separator in the middle, or D10 word.
                        error <= 1;
                        state <= HALTED;
                    end else begin
                        consecutive_twos <= 0;
                        accum_width <= accum_width + 1'b1;
                        accum_bits <= {accum_bits[7:0], trit[0]};
                    end
                    if ((trit == 2 && accum_width == 0 && consecutive_twos >= 4)
                        || (trit != 2 && (consecutive_twos > 1 || accum_width >= 9))) begin
                        state <= HALTED;
                    end else if (trit_index == 4) begin
                        state <= held_last ? FINISH : IDLE;
                    end else begin
                        trit_index <= trit_index + 1'b1;
                    end
                end
                FINISH: begin
                    if (accum_width != 0) begin
                        word_valid <= 1;
                        word_width <= accum_width;
                        word_bits <= accum_bits;
                        seen_word <= 1;
                        accum_width <= 0;
                        state <= FINISH_WAIT;
                    end else if (!seen_word) begin
                        error <= 1;
                        state <= HALTED;
                    end else begin
                        done <= 1;
                        state <= HALTED;
                    end
                end
                FINISH_WAIT: begin
                    done <= 1;
                    state <= HALTED;
                end
                default: state <= HALTED;
            endcase
        end
    end
endmodule

